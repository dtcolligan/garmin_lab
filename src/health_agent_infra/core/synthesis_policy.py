"""Synthesis-layer X-rule evaluators (Phase 2 step 4).

Deterministic cross-domain rule evaluation. Two phases:

  **Phase A** — runs over ``(snapshot, proposals)`` BEFORE the synthesis
  skill composes final recommendations. Tiers: ``soften``, ``block``,
  ``cap_confidence``. Output firings specify a ``recommended_mutation``
  the runtime applies mechanically to copy-on-write drafts; the skill
  never sees Phase A firings as "to be applied" — it sees them as
  "already applied" mutations on the drafts it receives.

  **Phase B** — runs over ``(snapshot, final_recommendations)`` AFTER the
  skill returns. Tier: ``adjust``. Strictly limited to
  ``action_detail`` mutations on a fixed registry of target domains. A
  write-surface guard (:func:`guard_phase_b_mutation`) rejects any
  firing that would touch ``action`` or a non-target domain.

All thresholds flow from :mod:`health_agent_infra.core.config` so a
user TOML can tune triggers without editing code. Rule bodies never
compute bands or scores themselves — they read the classified state the
domain runtime already produced and compare against configured numeric
thresholds.

This module has no I/O and no DB access. It operates on plain dicts
shaped like the synthesis bundle: ``snapshot`` is the
:func:`~health_agent_infra.core.state.snapshot.build_snapshot` output;
``proposals`` is a list of :class:`DomainProposal`-shaped dicts (as
emitted by ``hai propose``); ``drafts`` is a list of
:class:`BoundedRecommendation`-shaped dicts. The orchestration layer
in :mod:`health_agent_infra.core.synthesis` owns the I/O + mutation
application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Optional


Tier = Literal["soften", "block", "cap_confidence", "adjust", "restructure"]
Phase = Literal["A", "B"]


# ---------------------------------------------------------------------------
# Mutation-tier precedence. Higher number wins when two firings target the
# same (proposal_id, field). "block" (escalate) beats "soften" (downgrade)
# beats no-op. "cap_confidence" is independent — applied additively.
# ---------------------------------------------------------------------------
TIER_PRECEDENCE: dict[str, int] = {
    "soften": 1,
    "block": 2,
    "cap_confidence": 0,    # independent, not ordered with soften/block
    "adjust": 0,            # Phase B only
    "restructure": 3,       # reserved; not used in v1
}


# ---------------------------------------------------------------------------
# Domain action registries. Keyed by domain → (hard_actions, downgrade_action,
# escalate_action). "hard_actions" are the proposal actions that mean "I plan
# to train at the domain's baseline intensity" — they are the actions Phase A
# soften/block rules target. "downgrade_action" is the action a soften rule
# writes in. "escalate_action" is the action a block rule writes in.
# ---------------------------------------------------------------------------
_DOMAIN_ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    "recovery": {
        "hard_actions": frozenset({"proceed_with_planned_session"}),
        "downgrade_action": "downgrade_hard_session_to_zone_2",
        "escalate_action": "escalate_for_user_review",
    },
    "running": {
        "hard_actions": frozenset({"proceed_with_planned_run"}),
        "downgrade_action": "downgrade_to_easy_aerobic",
        "escalate_action": "escalate_for_user_review",
    },
}


# ---------------------------------------------------------------------------
# Phase B target registry — which rules may mutate which domains.
# Write-surface guard consults this. v1 holds only X9 → nutrition.
# ---------------------------------------------------------------------------
PHASE_B_TARGETS: dict[str, frozenset[str]] = {
    "X9": frozenset({"nutrition"}),
}


@dataclass(frozen=True)
class XRuleFiring:
    """One deterministic firing of a cross-domain X-rule.

    Attributes:
      rule_id: stable rule identifier (e.g. ``"X1a"``, ``"X3b"``, ``"X9"``).
      tier: the firing tier — ``soften``, ``block``, ``cap_confidence``
        (Phase A), or ``adjust`` (Phase B). Reserved: ``restructure``.
      affected_domain: the single domain whose proposal/recommendation
        is mutated by this firing. Rules that affect multiple domains
        emit multiple firings (one per domain).
      trigger_note: human-readable string describing the trigger, e.g.
        ``"sleep_debt_band=moderate with running proposal"``.
      recommended_mutation: either ``None`` (for ``cap_confidence``, which
        carries its cap in the tier name itself) or a dict shaped as
        ``{"action": ..., "action_detail": {...}}`` for soften/block, or
        ``{"action_detail": {...}}`` for Phase B ``adjust``.
      source_signals: the snapshot signals that drove the firing, kept
        as-is so the firing is self-documenting.
      phase: ``"A"`` or ``"B"``. Phase A firings are applied before the
        skill composes; Phase B firings are applied after.
    """

    rule_id: str
    tier: Tier
    affected_domain: str
    trigger_note: str
    recommended_mutation: Optional[dict[str, Any]]
    source_signals: dict[str, Any]
    phase: Phase

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "tier": self.tier,
            "affected_domain": self.affected_domain,
            "trigger_note": self.trigger_note,
            "recommended_mutation": self.recommended_mutation,
            "source_signals": dict(self.source_signals),
            "phase": self.phase,
        }


class XRuleWriteSurfaceViolation(ValueError):
    """Phase B firing attempted to mutate an off-limits field or domain.

    Guard invariant: Phase B rules may only mutate ``action_detail`` on a
    domain listed in :data:`PHASE_B_TARGETS[rule_id]`. Any other shape is
    a bug in the rule implementation and must be rejected loudly rather
    than silently corrupting the plan.
    """


# ===========================================================================
# Snapshot accessors — tolerant reads. Missing path ⇒ ``None``.
# ===========================================================================

def _get(d: Optional[dict[str, Any]], *path: str) -> Any:
    """Dotted-path getter that returns None on any missing step."""

    cur: Any = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _sleep_debt_band(snapshot: dict[str, Any]) -> Optional[str]:
    return _get(snapshot, "recovery", "classified_state", "sleep_debt_band")


def _acwr_ratio(snapshot: dict[str, Any]) -> Optional[float]:
    value = _get(snapshot, "recovery", "today", "acwr_ratio")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _body_battery(snapshot: dict[str, Any]) -> Optional[int]:
    """Read day-end body battery from the Phase 3 stress block.

    Body battery moved off ``accepted_recovery_state_daily`` onto
    ``accepted_stress_state_daily`` in migration 004. The snapshot
    surfaces it both on ``stress.today.body_battery_end_of_day`` and as
    the convenience key ``stress.today_body_battery``; this reader
    prefers the convenience key (cheaper, no nested get), falling back
    to the today row if only that is populated.
    """

    value = _get(snapshot, "stress", "today_body_battery")
    if value is None:
        value = _get(snapshot, "stress", "today", "body_battery_end_of_day")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stress_band(
    snapshot: dict[str, Any],
    thresholds: dict[str, Any],
) -> Optional[str]:
    """Derive a categorical stress band from the Phase 3 stress block.

    Reads ``stress.today_garmin`` (Garmin's numeric 0-100 all-day stress)
    as the X7 input. Migration 004 moved this signal off the recovery
    accepted row onto ``accepted_stress_state_daily.garmin_all_day_stress``;
    the snapshot exposes it as the convenience key ``stress.today_garmin``.

    X7 still bands locally using the same numeric thresholds as pre-
    Phase-3. Once the stress domain ships a dedicated
    ``classify_stress_state`` (Phase 3 step 4) this reader will prefer
    ``stress.classified_state.garmin_stress_band`` and fall back to the
    local banding as a defensive second path — the band computation
    moves to the domain but X7's trigger registry stays here.
    """

    classified_band = _get(snapshot, "stress", "classified_state", "garmin_stress_band")
    if classified_band is not None:
        return classified_band

    value = _get(snapshot, "stress", "today_garmin")
    if value is None:
        value = _get(snapshot, "stress", "today", "garmin_all_day_stress")
    if value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    x7_cfg = _get(thresholds, "synthesis", "x_rules", "x7") or {}
    very_high_min = int(x7_cfg.get("very_high_min_score", 80))
    high_min = int(x7_cfg.get("high_min_score", 60))
    moderate_min = int(x7_cfg.get("moderate_min_score", 40))
    if score >= very_high_min:
        return "very_high"
    if score >= high_min:
        return "high"
    if score >= moderate_min:
        return "moderate"
    return "low"


def _is_hard_proposal(proposal: dict[str, Any]) -> bool:
    """True when the proposal's action is the domain's baseline-hard action.

    A proposal that has already been softened or escalated at policy time
    (e.g. ``downgrade_intervals_to_tempo``, ``rest_day_recommended``,
    ``escalate_for_user_review``) is not "hard" and no further soften/block
    rule fires against it. This keeps X-rule mutations idempotent across
    re-runs.
    """

    domain = proposal.get("domain")
    registry = _DOMAIN_ACTION_REGISTRY.get(domain)
    if registry is None:
        return False
    return proposal.get("action") in registry["hard_actions"]


# ===========================================================================
# Phase A rules
# ===========================================================================

def evaluate_x1a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X1a (soften): sleep_debt at configured trigger → downgrade hard sessions.

    Trigger: ``recovery.classified_state.sleep_debt_band`` equals the
    config-keyed band (default ``"moderate"``). Affects every hard
    proposal in the bundle.
    """

    trigger_band = _get(thresholds, "synthesis", "x_rules", "x1a", "sleep_debt_trigger_band")
    sleep_debt = _sleep_debt_band(snapshot)
    if sleep_debt is None or sleep_debt != trigger_band:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X1a",
            tier="soften",
            affected_domain=domain,
            trigger_note=(
                f"sleep_debt_band={sleep_debt} with hard {domain} proposal "
                f"(action={p.get('action')})"
            ),
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x1a_sleep_debt_trigger",
                    "trigger_band": sleep_debt,
                },
            },
            source_signals={
                "sleep_debt_band": sleep_debt,
                "proposal_domain": domain,
                "proposal_action": p.get("action"),
            },
            phase="A",
        ))
    return firings


def evaluate_x1b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X1b (block): elevated sleep debt → escalate hard sessions.

    Trigger: ``sleep_debt_band`` equals the config-keyed band (default
    ``"elevated"``). Forces escalate on every hard proposal.
    """

    trigger_band = _get(thresholds, "synthesis", "x_rules", "x1b", "sleep_debt_trigger_band")
    sleep_debt = _sleep_debt_band(snapshot)
    if sleep_debt is None or sleep_debt != trigger_band:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X1b",
            tier="block",
            affected_domain=domain,
            trigger_note=(
                f"sleep_debt_band={sleep_debt} with hard {domain} proposal"
            ),
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x1b_sleep_debt_elevated",
                    "trigger_band": sleep_debt,
                },
            },
            source_signals={
                "sleep_debt_band": sleep_debt,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x3a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X3a (soften): 1.3 ≤ acwr_ratio < 1.5 → downgrade hard sessions."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x3a") or {}
    lower = float(cfg.get("acwr_ratio_lower", 1.3))
    upper = float(cfg.get("acwr_ratio_upper", 1.5))
    acwr = _acwr_ratio(snapshot)
    if acwr is None or not (lower <= acwr < upper):
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X3a",
            tier="soften",
            affected_domain=domain,
            trigger_note=f"acwr_ratio={acwr:.3f} in [{lower}, {upper}) with hard {domain} proposal",
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x3a_acwr_elevated",
                    "acwr_ratio": acwr,
                },
            },
            source_signals={
                "acwr_ratio": acwr,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x3b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X3b (block): acwr_ratio ≥ 1.5 → escalate hard sessions."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x3b") or {}
    minimum = float(cfg.get("acwr_ratio_min", 1.5))
    acwr = _acwr_ratio(snapshot)
    if acwr is None or acwr < minimum:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X3b",
            tier="block",
            affected_domain=domain,
            trigger_note=f"acwr_ratio={acwr:.3f} ≥ {minimum} with hard {domain} proposal",
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x3b_acwr_spike",
                    "acwr_ratio": acwr,
                },
            },
            source_signals={
                "acwr_ratio": acwr,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x6a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X6a (soften): body_battery < 30 → downgrade every hard proposal."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x6a") or {}
    ceiling = int(cfg.get("body_battery_max", 30))
    bb = _body_battery(snapshot)
    if bb is None or bb >= ceiling:
        return []

    # X6b also reads body_battery; if its (lower) threshold fires, skip X6a
    # for the same proposal to avoid double-downgrading. X6b's block tier
    # wins via precedence anyway, but suppressing the duplicate keeps the
    # firings list clean.
    x6b_cfg = _get(thresholds, "synthesis", "x_rules", "x6b") or {}
    x6b_ceiling = int(x6b_cfg.get("body_battery_max", 15))
    if bb < x6b_ceiling:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X6a",
            tier="soften",
            affected_domain=domain,
            trigger_note=f"body_battery_end_of_day={bb} < {ceiling} (depleted reserve)",
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x6a_body_battery_low",
                    "body_battery_end_of_day": bb,
                },
            },
            source_signals={
                "body_battery_end_of_day": bb,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x6b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X6b (block): body_battery < 15 → escalate every hard proposal."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x6b") or {}
    ceiling = int(cfg.get("body_battery_max", 15))
    bb = _body_battery(snapshot)
    if bb is None or bb >= ceiling:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X6b",
            tier="block",
            affected_domain=domain,
            trigger_note=f"body_battery_end_of_day={bb} < {ceiling} (severely depleted)",
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x6b_body_battery_critical",
                    "body_battery_end_of_day": bb,
                },
            },
            source_signals={
                "body_battery_end_of_day": bb,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x7(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X7 (cap_confidence): elevated stress → cap confidence at moderate.

    No action mutation — only caps confidence on every proposal's final
    recommendation. Applies regardless of whether the proposal is "hard".
    """

    cfg = _get(thresholds, "synthesis", "x_rules", "x7") or {}
    trigger_bands = set(cfg.get("stress_trigger_bands") or [])
    band = _stress_band(snapshot, thresholds)
    if band is None or band not in trigger_bands:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        domain = p.get("domain")
        if not domain:
            continue
        firings.append(XRuleFiring(
            rule_id="X7",
            tier="cap_confidence",
            affected_domain=domain,
            trigger_note=f"stress_band={band} ∈ {sorted(trigger_bands)}",
            recommended_mutation=None,  # cap is implicit in tier
            source_signals={
                "stress_band": band,
                "garmin_all_day_stress": _get(snapshot, "stress", "today_garmin"),
            },
            phase="A",
        ))
    return firings


PHASE_A_EVALUATORS = (
    evaluate_x1a,
    evaluate_x1b,
    evaluate_x3a,
    evaluate_x3b,
    evaluate_x6a,
    evaluate_x6b,
    evaluate_x7,
)


def evaluate_phase_a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """Run every Phase A rule and return the concatenated firings list.

    Order matches :data:`PHASE_A_EVALUATORS`. The orchestration layer
    applies mutations with tier precedence (block > soften); the order
    here is therefore informational and does not affect final drafts.
    """

    firings: list[XRuleFiring] = []
    for evaluator in PHASE_A_EVALUATORS:
        firings.extend(evaluator(snapshot, proposals, thresholds))
    return firings


# ===========================================================================
# Phase B rules — action_detail adjustments only, guarded write surface
# ===========================================================================

def evaluate_x9(
    snapshot: dict[str, Any],
    drafts: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X9 (adjust): training intensity → nutrition target adjustments.

    v1 scope: operates only on ``nutrition`` drafts. For every draft in
    the nutrition domain, if any training-domain draft (recovery or
    running) carries a "hard" baseline action, append a note to the
    nutrition ``action_detail`` bumping protein / carb targets.

    Until the nutrition domain lands, this evaluator returns ``[]``
    because no nutrition draft can appear in the input. The machinery
    exists so Phase B has at least one evaluator to exercise + test.
    """

    nutrition_drafts = [d for d in drafts if d.get("domain") == "nutrition"]
    if not nutrition_drafts:
        return []

    training_hard = any(
        d.get("domain") in ("recovery", "running") and _is_hard_proposal(d)
        for d in drafts
    )
    if not training_hard:
        return []

    firings: list[XRuleFiring] = []
    for d in nutrition_drafts:
        firings.append(XRuleFiring(
            rule_id="X9",
            tier="adjust",
            affected_domain="nutrition",
            trigger_note="training_intensity=hard → nutrition target adjustment",
            recommended_mutation={
                "action_detail": {
                    "reason_token": "x9_training_intensity_bump",
                    "protein_target_multiplier": 1.1,
                },
            },
            source_signals={
                "training_intensity": "hard",
                "nutrition_domain": d.get("domain"),
            },
            phase="B",
        ))
    return firings


PHASE_B_EVALUATORS = (
    evaluate_x9,
)


def evaluate_phase_b(
    snapshot: dict[str, Any],
    drafts: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """Run every Phase B rule and return firings. Does NOT apply mutations.

    Callers run :func:`guard_phase_b_mutation` and then :func:`apply_phase_b`
    to mutate drafts. The split lets tests assert against the raw firing
    list before mutation application.
    """

    firings: list[XRuleFiring] = []
    for evaluator in PHASE_B_EVALUATORS:
        firings.extend(evaluator(snapshot, drafts, thresholds))
    return firings


def guard_phase_b_mutation(firing: XRuleFiring) -> None:
    """Reject any Phase B firing that violates the write-surface contract.

    Raises :class:`XRuleWriteSurfaceViolation` on:

      - tier not equal to ``"adjust"``
      - ``affected_domain`` not in :data:`PHASE_B_TARGETS[rule_id]`
      - ``recommended_mutation`` touching ``action`` (Phase B may only
        mutate ``action_detail``)
      - ``recommended_mutation`` being ``None`` (every Phase B firing
        must carry a concrete mutation — caps are Phase A only)

    Runs at mutation-application time in the orchestration layer.
    """

    if firing.phase != "B":
        raise XRuleWriteSurfaceViolation(
            f"guard_phase_b_mutation called on non-B firing {firing.rule_id!r}"
        )
    if firing.tier != "adjust":
        raise XRuleWriteSurfaceViolation(
            f"Phase B tier must be 'adjust'; got {firing.tier!r} on {firing.rule_id!r}"
        )
    allowed_domains = PHASE_B_TARGETS.get(firing.rule_id)
    if allowed_domains is None:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} has no target registry entry"
        )
    if firing.affected_domain not in allowed_domains:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} tried to touch domain "
            f"{firing.affected_domain!r} — allowed: {sorted(allowed_domains)}"
        )
    mutation = firing.recommended_mutation
    if not isinstance(mutation, dict):
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} must carry a dict mutation; "
            f"got {type(mutation).__name__}"
        )
    if "action" in mutation:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} attempted to mutate 'action' — "
            f"Phase B may only mutate 'action_detail'"
        )
    if "action_detail" not in mutation:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} mutation must contain 'action_detail'"
        )


# ===========================================================================
# Mutation application helpers
# ===========================================================================

def apply_phase_a(
    proposal: dict[str, Any],
    firings: Iterable[XRuleFiring],
) -> tuple[dict[str, Any], list[str]]:
    """Return ``(mutated_proposal, fired_rule_ids)`` for a single proposal.

    Precedence:
      1. ``block`` tier wins over ``soften`` tier. If any block firing
         targets this proposal, the block mutation is applied and any
         soften firings are recorded-as-fired but not applied.
      2. ``cap_confidence`` firings apply independently — they lower
         ``confidence`` to ``"moderate"`` when the current confidence is
         ``"high"``. They never raise.
      3. If multiple block firings target the same proposal, the first
         one in iteration order wins (stable). Ditto multiple softens.

    Returns the mutated proposal as a fresh dict; the input is not
    modified. ``fired_rule_ids`` lists every rule id that matched this
    proposal (including capped-by-precedence softens) so the firings
    table receives a complete audit trail.
    """

    proposal_domain = proposal.get("domain")
    relevant = [f for f in firings if f.affected_domain == proposal_domain]

    blocks = [f for f in relevant if f.tier == "block"]
    softens = [f for f in relevant if f.tier == "soften"]
    caps = [f for f in relevant if f.tier == "cap_confidence"]

    mutated = dict(proposal)
    if "action_detail" in mutated and isinstance(mutated["action_detail"], dict):
        mutated["action_detail"] = dict(mutated["action_detail"])

    applied_action_mutation = False
    # Precedence: block > soften.
    if blocks:
        block = blocks[0]
        mutation = block.recommended_mutation or {}
        if "action" in mutation:
            mutated["action"] = mutation["action"]
        if "action_detail" in mutation:
            mutated["action_detail"] = dict(mutation["action_detail"])
        applied_action_mutation = True
    elif softens:
        soften = softens[0]
        mutation = soften.recommended_mutation or {}
        if "action" in mutation:
            mutated["action"] = mutation["action"]
        if "action_detail" in mutation:
            mutated["action_detail"] = dict(mutation["action_detail"])
        applied_action_mutation = True

    # cap_confidence: independent. Lower "high" to "moderate"; never raise.
    if caps:
        current = mutated.get("confidence")
        if current == "high":
            mutated["confidence"] = "moderate"

    fired_ids = [f.rule_id for f in relevant]
    return mutated, fired_ids


def apply_phase_b(
    draft: dict[str, Any],
    firings: Iterable[XRuleFiring],
) -> tuple[dict[str, Any], list[str]]:
    """Return ``(mutated_draft, fired_rule_ids)`` after Phase B.

    Every firing is guarded by :func:`guard_phase_b_mutation` before
    application. Mutations merge into ``action_detail`` (not replace);
    keys from later firings overwrite earlier ones on collision.
    """

    domain = draft.get("domain")
    relevant = [f for f in firings if f.affected_domain == domain]
    if not relevant:
        return dict(draft), []

    mutated = dict(draft)
    detail = dict(mutated.get("action_detail") or {})
    fired_ids: list[str] = []
    for firing in relevant:
        guard_phase_b_mutation(firing)
        mutation = firing.recommended_mutation or {}
        incoming_detail = mutation.get("action_detail") or {}
        detail.update(incoming_detail)
        fired_ids.append(firing.rule_id)

    mutated["action_detail"] = detail
    return mutated, fired_ids
