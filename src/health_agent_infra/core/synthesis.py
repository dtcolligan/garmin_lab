"""Synthesis orchestration (Phase 2 step 4).

Glues :mod:`health_agent_infra.core.synthesis_policy` to the DB + JSONL
side. One function — :func:`run_synthesis` — is called by
``hai synthesize``. Everything it does in a single SQLite BEGIN/COMMIT:

  1. Read snapshot for ``(for_date, user_id)`` from the DB.
  2. Read every proposal in ``proposal_log`` for ``(for_date, user_id)``.
  3. Run Phase A — X1a, X1b, X2, X3a, X3b, X4, X5, X6a, X6b, X7
     (the full ``PHASE_A_EVALUATORS`` tuple in
     :mod:`core.synthesis_policy`).
  4. Apply Phase A mutations mechanically → draft BoundedRecommendations.
  5. Overlay skill-authored rationale + uncertainty if ``drafts_json``
     was provided (the skill's judgment layer). Skill cannot change
     ``action`` / ``action_detail`` / ``confidence`` — those are
     runtime-owned after Phase A.
  6. Run Phase B — X9. Apply mutations via :func:`apply_phase_b` with
     :func:`guard_phase_b_mutation` enforcing the write-surface
     contract.
  7. Write ``daily_plan`` + N ``recommendation_log`` rows + M
     ``x_rule_firing`` rows + link ``proposal_log.daily_plan_id`` — all
     in one SQLite transaction. A failure anywhere rolls the whole
     thing back.

**Idempotency + supersession.**

- Default: re-running for the same ``(for_date, user_id)`` replaces the
  prior canonical plan atomically — old plan + firings + recommendations
  are deleted and new ones inserted in the same transaction.
- ``supersede=True``: the prior plan stays; its ``superseded_by`` pointer
  is flipped to the new plan's id; the new plan is written under a fresh
  ``_v<N>`` id (deterministic: count existing ``_v<N>`` plans for that
  key, pick next).

**Error surface.**

- :class:`SynthesisError` — bundle inputs don't satisfy preconditions
  (no proposals, proposal validation failure, etc.).
- :class:`XRuleWriteSurfaceViolation` — a Phase B rule attempted an
  off-limits mutation. Bubbles up from the policy layer.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.core.schemas import (
    RECOMMENDATION_SCHEMA_VERSION,
    canonical_daily_plan_id,
)
from health_agent_infra.core.state.projector import (
    delete_canonical_plan_cascade,
    link_proposal_to_plan,
    mark_plan_superseded,
    project_bounded_recommendation,
    project_daily_plan,
    project_planned_recommendation,
    project_x_rule_firing,
    read_proposals_for_plan_key,
)
from health_agent_infra.core.state.snapshot import build_snapshot
from health_agent_infra.core.synthesis_policy import (
    XRuleFiring,
    XRuleWriteSurfaceViolation,
    apply_phase_a,
    apply_phase_b,
    evaluate_phase_a,
    evaluate_phase_b,
    guard_phase_b_mutation,
)


RECOMMENDATION_SCHEMA_BY_DOMAIN: dict[str, str] = {
    "recovery": "training_recommendation.v1",
    "running": "running_recommendation.v1",
    "sleep": "sleep_recommendation.v1",
    "stress": "stress_recommendation.v1",
    "strength": "strength_recommendation.v1",
    "nutrition": "nutrition_recommendation.v1",
}


class SynthesisError(RuntimeError):
    """Raised when synthesis preconditions fail."""


@dataclass
class SynthesisResult:
    daily_plan_id: str
    recommendation_ids: list[str]
    proposal_ids: list[str]
    phase_a_firings: list[XRuleFiring]
    phase_b_firings: list[XRuleFiring]
    superseded_prior: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_plan_id": self.daily_plan_id,
            "recommendation_ids": list(self.recommendation_ids),
            "proposal_ids": list(self.proposal_ids),
            "phase_a_firings": [f.to_dict() for f in self.phase_a_firings],
            "phase_b_firings": [f.to_dict() for f in self.phase_b_firings],
            "superseded_prior": self.superseded_prior,
        }


# ---------------------------------------------------------------------------
# Draft construction — mechanically transform proposals into
# BoundedRecommendation-shaped drafts before the skill sees them.
# ---------------------------------------------------------------------------

def _mechanical_draft(
    proposal: dict[str, Any],
    *,
    daily_plan_id: str,
    issued_at: datetime,
    agent_version: str,
    plan_version_suffix: str = "",
) -> dict[str, Any]:
    """Convert a proposal dict to a draft BoundedRecommendation dict.

    The runtime synthesises the missing fields (``recommendation_id``,
    ``follow_up``, ``daily_plan_id``) deterministically so this function
    stays pure. Rationale and uncertainty are copied verbatim from the
    proposal and can be replaced by the skill's drafts-json overlay.

    ``plan_version_suffix`` is appended to the recommendation id to keep
    superseded plan recommendations collision-free in
    ``recommendation_log`` (the table's PK is ``recommendation_id`` only).
    Empty on the canonical plan path.
    """

    recommendation_id = (
        f"rec_{proposal['for_date']}_{proposal['user_id']}_"
        f"{proposal['domain']}_01{plan_version_suffix}"
    )
    review_at = issued_at + timedelta(hours=23)
    review_event_id = f"rev_{proposal['for_date']}_{proposal['user_id']}_{recommendation_id}"

    return {
        "schema_version": RECOMMENDATION_SCHEMA_BY_DOMAIN.get(
            proposal["domain"], RECOMMENDATION_SCHEMA_VERSION,
        ),
        "recommendation_id": recommendation_id,
        "user_id": proposal["user_id"],
        "issued_at": issued_at.isoformat(),
        "for_date": proposal["for_date"],
        "domain": proposal["domain"],
        "action": proposal["action"],
        "action_detail": proposal.get("action_detail"),
        "rationale": list(proposal.get("rationale") or []),
        "confidence": proposal["confidence"],
        "uncertainty": list(proposal.get("uncertainty") or []),
        "follow_up": {
            "review_at": review_at.isoformat(),
            "review_question": _default_review_question(
                proposal["action"], proposal["domain"],
            ),
            "review_event_id": review_event_id,
        },
        "policy_decisions": list(proposal.get("policy_decisions") or []),
        "bounded": True,
        "daily_plan_id": daily_plan_id,
    }


_DEFAULT_REVIEW_QUESTIONS: dict[str, str] = {
    "proceed_with_planned_session": "Did today's session feel appropriate for your recovery?",
    "proceed_with_planned_run": "Did today's run feel appropriate for your current form?",
    "downgrade_hard_session_to_zone_2": "Did yesterday's downgrade to Zone 2 improve how today feels?",
    "downgrade_session_to_mobility_only": "Did yesterday's mobility-only day help your recovery?",
    "downgrade_intervals_to_tempo": "Did yesterday's tempo session land well?",
    "downgrade_to_easy_aerobic": "Did the easy run yesterday leave you feeling better today?",
    "cross_train_instead": "Did the cross-training session suit your recovery?",
    "rest_day_recommended": "Did yesterday's rest day help your recovery?",
    "defer_decision_insufficient_signal": "Did you decide on a session yesterday? How did it go?",
    "escalate_for_user_review": "You had a persistent signal we flagged. Did you take any action?",
    # Sleep (Phase 3 step 5)
    "maintain_schedule": "Did sticking with your usual sleep schedule feel right last night?",
    "prioritize_wind_down": "Did the earlier wind-down help last night's sleep?",
    "sleep_debt_repayment_day": "Were you able to log extra sleep to repay the debt?",
    "earlier_bedtime_target": "Were you able to hit the earlier bedtime target?",
    # Stress (Phase 3 step 5)
    "maintain_routine": "Did your usual routine feel right given yesterday's stress signals?",
    "add_low_intensity_recovery": "Did the low-intensity recovery block help yesterday?",
    "schedule_decompression_time": "Were you able to take the decompression time you planned?",
    # Strength (Phase 7 closure: strength wired as a real proposal/synthesis
    # domain). ``proceed_with_planned_session`` is shared with recovery; the
    # per-domain override below gives strength a domain-appropriate prompt
    # without touching the recovery wording any existing test / artifact
    # captures depend on.
    "downgrade_to_technique_or_accessory": "Did yesterday's technique / accessory work land well?",
    "downgrade_to_moderate_load": "Did yesterday's moderate-load session feel appropriate?",
    # Nutrition (Phase 5 step 4)
    "maintain_targets": "Did yesterday's macro targets feel sustainable?",
    "increase_protein_intake": "Were you able to hit the higher protein target yesterday?",
    "increase_hydration": "Did the extra fluids help yesterday?",
    "reduce_calorie_deficit": "Did yesterday's adjusted intake feel right for your training?",
}


# Per-(domain, action) overrides for actions whose enum value is shared
# across domains but whose natural review question differs. Looked up
# before the action-only map so existing domain wordings stay intact.
_DOMAIN_REVIEW_QUESTION_OVERRIDES: dict[tuple[str, str], str] = {
    ("strength", "proceed_with_planned_session"):
        "Did today's planned strength session feel appropriate?",
    ("strength", "rest_day_recommended"):
        "Did yesterday's rest day leave you fresh for the next lift?",
}


def _default_review_question(action: str, domain: str = "recovery") -> str:
    override = _DOMAIN_REVIEW_QUESTION_OVERRIDES.get((domain, action))
    if override is not None:
        return override
    return _DEFAULT_REVIEW_QUESTIONS.get(
        action, "How did yesterday's plan work out?",
    )


def _overlay_skill_drafts(
    drafts: list[dict[str, Any]],
    skill_drafts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Overlay skill-authored rationale + uncertainty onto mechanical drafts.

    The skill may only edit fields that belong to its judgment layer:
    ``rationale``, ``uncertainty``, and ``follow_up.review_question``.
    Any skill attempt to edit ``action``, ``action_detail``,
    ``confidence``, or ``daily_plan_id`` is silently ignored — those
    are runtime-owned after Phase A mutation application.

    Skill drafts are keyed by ``recommendation_id`` for matching; the
    overlay is best-effort (missing skill draft ⇒ mechanical draft
    stands).
    """

    by_id = {d.get("recommendation_id"): d for d in skill_drafts if d.get("recommendation_id")}
    out: list[dict[str, Any]] = []
    for draft in drafts:
        skill_draft = by_id.get(draft["recommendation_id"])
        if skill_draft is None:
            out.append(draft)
            continue
        merged = dict(draft)
        if isinstance(skill_draft.get("rationale"), list):
            merged["rationale"] = list(skill_draft["rationale"])
        if isinstance(skill_draft.get("uncertainty"), list):
            merged["uncertainty"] = list(skill_draft["uncertainty"])
        incoming_fu = skill_draft.get("follow_up") or {}
        if isinstance(incoming_fu, dict) and "review_question" in incoming_fu:
            fu = dict(merged["follow_up"])
            fu["review_question"] = incoming_fu["review_question"]
            merged["follow_up"] = fu
        out.append(merged)
    return out


# ---------------------------------------------------------------------------
# Plan id supersession helpers
# ---------------------------------------------------------------------------

def _next_superseded_plan_id(
    conn: sqlite3.Connection,
    *,
    canonical_id: str,
) -> str:
    """Pick the next ``<canonical>_v<N>`` suffix not yet in ``daily_plan``.

    N = 2 on first supersession (``_v2``), 3 next, etc. Canonical id
    itself is reserved for the default-idempotent path — supersession
    always assigns a suffixed variant.
    """

    rows = conn.execute(
        "SELECT daily_plan_id FROM daily_plan WHERE daily_plan_id LIKE ?",
        (f"{canonical_id}_v%",),
    ).fetchall()
    existing_suffixes: set[int] = set()
    for row in rows:
        suffix = row["daily_plan_id"].rsplit("_v", 1)[-1]
        try:
            existing_suffixes.add(int(suffix))
        except ValueError:
            continue
    # Canonical counts as v1 for the purposes of picking the next suffix.
    n = 2
    while n in existing_suffixes:
        n += 1
    return f"{canonical_id}_v{n}"


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_synthesis(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
    snapshot: Optional[dict[str, Any]] = None,
    skill_drafts: Optional[list[dict[str, Any]]] = None,
    thresholds: Optional[dict[str, Any]] = None,
    agent_version: str = "claude_agent_v1",
    now: Optional[datetime] = None,
    supersede: bool = False,
) -> SynthesisResult:
    """Run synthesis end-to-end inside a single SQLite transaction.

    ``snapshot`` defaults to :func:`build_snapshot(conn, for_date, user_id)`
    if not supplied. Tests pass a synthetic snapshot dict.

    ``skill_drafts`` lets callers feed the skill's judgment overlay as a
    list of partial BoundedRecommendation dicts. When None, drafts are
    purely mechanical — action, confidence, and follow_up are all set by
    the runtime.

    ``thresholds`` falls through to
    :func:`health_agent_infra.core.config.load_thresholds` when None.

    ``supersede=False`` (default) → replace prior canonical plan.
    ``supersede=True`` → keep prior plan, write new one at
    ``<canonical_id>_v<N>``, flip ``superseded_by`` pointer on prior.
    """

    if snapshot is None:
        snapshot = build_snapshot(
            conn, as_of_date=for_date, user_id=user_id, lookback_days=14,
        )
    if thresholds is None:
        thresholds = load_thresholds()
    now = now or datetime.now(timezone.utc)

    for_date_iso = for_date.isoformat()
    proposals = read_proposals_for_plan_key(
        conn, for_date=for_date_iso, user_id=user_id,
    )
    if not proposals:
        raise SynthesisError(
            f"no proposals in proposal_log for (for_date={for_date_iso}, "
            f"user_id={user_id!r}). Call `hai propose` first."
        )

    # Phase A
    phase_a_firings = evaluate_phase_a(snapshot, proposals, thresholds)

    canonical_id = canonical_daily_plan_id(for_date, user_id)
    if supersede:
        daily_plan_id = _next_superseded_plan_id(conn, canonical_id=canonical_id)
        plan_version_suffix = daily_plan_id[len(canonical_id):]  # e.g. "_v2"
    else:
        daily_plan_id = canonical_id
        plan_version_suffix = ""

    # Phase 1 (agent-operable runtime plan §1) — capture the
    # pre-X-rule aggregate BEFORE apply_phase_a mutates anything. Each
    # planned_recommendation row mirrors the draft we'd have committed if
    # no X-rule had fired. Written inside the atomic transaction below
    # so the planned/adapted pair is always consistent.
    planned_rows: list[dict[str, Any]] = []
    for proposal in proposals:
        planned_draft = _mechanical_draft(
            proposal,
            daily_plan_id=daily_plan_id,
            issued_at=now,
            agent_version=agent_version,
            plan_version_suffix=plan_version_suffix,
        )
        planned_rows.append({
            "planned_id": (
                f"planned_{proposal['for_date']}_{proposal['user_id']}_"
                f"{proposal['domain']}_01{plan_version_suffix}"
            ),
            "daily_plan_id": daily_plan_id,
            "proposal_id": proposal["proposal_id"],
            "user_id": proposal["user_id"],
            "for_date": proposal["for_date"],
            "domain": proposal["domain"],
            "action": planned_draft["action"],
            "confidence": planned_draft["confidence"],
            "action_detail": planned_draft.get("action_detail"),
            "captured_at": now.isoformat(),
        })

    # Draft construction + skill overlay
    drafts: list[dict[str, Any]] = []
    for proposal in proposals:
        mutated_proposal, _fired = apply_phase_a(proposal, phase_a_firings)
        draft = _mechanical_draft(
            mutated_proposal,
            daily_plan_id=daily_plan_id,
            issued_at=now,
            agent_version=agent_version,
            plan_version_suffix=plan_version_suffix,
        )
        drafts.append(draft)

    if skill_drafts is not None:
        drafts = _overlay_skill_drafts(drafts, skill_drafts)

    # Phase B — evaluate, guard, apply.
    phase_b_firings = evaluate_phase_b(snapshot, drafts, thresholds)
    for firing in phase_b_firings:
        guard_phase_b_mutation(firing)
    final_recommendations: list[dict[str, Any]] = []
    for draft in drafts:
        mutated, _fired_b = apply_phase_b(draft, phase_b_firings)
        final_recommendations.append(mutated)

    proposal_ids = [p["proposal_id"] for p in proposals]
    recommendation_ids = [r["recommendation_id"] for r in final_recommendations]
    all_firings = [*phase_a_firings, *phase_b_firings]

    plan_dict = {
        "daily_plan_id": daily_plan_id,
        "user_id": user_id,
        "for_date": for_date_iso,
        "synthesized_at": now.isoformat(),
        "recommendation_ids": recommendation_ids,
        "proposal_ids": proposal_ids,
        "x_rules_fired": sorted({f.rule_id for f in all_firings}),
        "synthesis_meta": {
            "phase_a_count": len(phase_a_firings),
            "phase_b_count": len(phase_b_firings),
            "supersede": supersede,
        },
        "agent_version": agent_version,
    }

    superseded_prior: Optional[str] = None

    # Atomic commit.
    conn.execute("BEGIN EXCLUSIVE")
    try:
        if supersede:
            prior = conn.execute(
                "SELECT daily_plan_id FROM daily_plan WHERE daily_plan_id = ?",
                (canonical_id,),
            ).fetchone()
            if prior is not None:
                mark_plan_superseded(
                    conn,
                    daily_plan_id=canonical_id,
                    superseded_by=daily_plan_id,
                    commit_after=False,
                )
                superseded_prior = canonical_id
        else:
            delete_canonical_plan_cascade(
                conn, daily_plan_id=canonical_id, commit_after=False,
            )

        project_daily_plan(
            conn, plan_dict, commit_after=False,
        )

        # Phase 2.5 Condition 1 — orphan defensive check. A firing whose
        # affected_domain is not in the committing plan's proposal domains
        # is stamped orphan=1 so future regressions (e.g. a rule that
        # emits firings from snapshot-only signals without iterating
        # proposals) surface in the audit table rather than silently
        # leaving dead rows. Current rules cannot emit orphans by
        # construction, so this is a monitor, not a gate.
        proposal_domains = {p["domain"] for p in proposals}
        for firing in all_firings:
            is_orphan = firing.affected_domain not in proposal_domains
            project_x_rule_firing(
                conn,
                firing.to_dict(),
                daily_plan_id=daily_plan_id,
                user_id=user_id,
                orphan=is_orphan,
                commit_after=False,
            )

        for recommendation in final_recommendations:
            project_bounded_recommendation(
                conn,
                recommendation,
                agent_version=agent_version,
                commit_after=False,
            )

        for proposal_id in proposal_ids:
            link_proposal_to_plan(
                conn,
                proposal_id=proposal_id,
                daily_plan_id=daily_plan_id,
                commit_after=False,
            )

        # Planned-recommendation ledger rows: written last so both FK
        # parents are populated — daily_plan by project_daily_plan above,
        # proposal_log.daily_plan_id by link_proposal_to_plan immediately
        # before this. The planned-row set is derived from the ORIGINAL
        # (pre-mutation) proposals, so rollback semantics hold: if any
        # prior insert fails the planned rows never land.
        for planned_row in planned_rows:
            project_planned_recommendation(
                conn,
                planned_row,
                agent_version=agent_version,
                commit_after=False,
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return SynthesisResult(
        daily_plan_id=daily_plan_id,
        recommendation_ids=recommendation_ids,
        proposal_ids=proposal_ids,
        phase_a_firings=phase_a_firings,
        phase_b_firings=phase_b_firings,
        superseded_prior=superseded_prior,
    )


# ---------------------------------------------------------------------------
# Bundle emission for the skill (read-only; no DB writes)
# ---------------------------------------------------------------------------

def build_synthesis_bundle(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
    thresholds: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Return ``{"snapshot", "proposals", "phase_a_firings"}`` for the skill.

    The skill reads this bundle to understand what mutations the runtime
    will apply, then composes rationale + uncertainty on top. The skill
    never sees Phase B firings (those run after the skill returns).
    """

    if thresholds is None:
        thresholds = load_thresholds()
    snapshot = build_snapshot(
        conn, as_of_date=for_date, user_id=user_id, lookback_days=14,
    )
    proposals = read_proposals_for_plan_key(
        conn, for_date=for_date.isoformat(), user_id=user_id,
    )
    firings = evaluate_phase_a(snapshot, proposals, thresholds)
    return {
        "snapshot": snapshot,
        "proposals": proposals,
        "phase_a_firings": [f.to_dict() for f in firings],
    }
