"""Phase A safety closure tests — v0.1.4 blocking.

Pins the runtime invariant Codex flagged in the 2026-04-24 strategic
report: every final recommendation persisted by the canonical
``run_synthesis`` path must pass the same banned-token + shape validator
that the (now-retired) ``hai writeback`` path enforced. Without this,
the project's first stated success criterion — "no final recommendation
can bypass safety validation" — is silently false on the canonical
write path.

Coverage required by the brief:
  1. Banned token in proposal-derived rationale → reject synthesis.
  2. Banned token in skill draft overlay rationale → reject.
  3. Banned token in skill draft overlay uncertainty → reject.
  4. Banned token in action_detail → reject.
  5. Banned token in follow_up.review_question → reject (after the runtime
     composes it from the per-domain template + skill overlay).
  6. Atomic rollback: failed synthesis leaves daily_plan,
     recommendation_log, x_rule_firing, planned_recommendation, and
     proposal_log.daily_plan_id unchanged.
  7. Defensive guard: more than one canonical-leaf proposal for the same
     ``(for_date, user_id, domain)`` → reject before commit, no DB writes.
  8. All six domains pass valid recommendation validation end-to-end.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import SynthesisError, run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 22)
USER = "u_safety"


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

# Per-domain "clean default" actions — first non-defer action in each
# domain's enum so each builder produces a recommendation that exercises
# a real action path, not the catch-all defer.
_DEFAULT_ACTIONS: dict[str, str] = {
    "recovery": "proceed_with_planned_session",
    "running": "proceed_with_planned_run",
    "sleep": "maintain_schedule",
    "strength": "proceed_with_planned_session",
    "stress": "maintain_routine",
    "nutrition": "maintain_targets",
}


def _make_proposal(
    domain: str,
    *,
    action: str | None = None,
    confidence: str = "high",
    rationale: list[str] | None = None,
    uncertainty: list[str] | None = None,
    action_detail: dict | None = None,
    proposal_id: str | None = None,
) -> dict:
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": proposal_id or f"prop_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": action or _DEFAULT_ACTIONS[domain],
        "action_detail": action_detail,
        "rationale": rationale if rationale is not None else [f"{domain}_baseline"],
        "confidence": confidence,
        "uncertainty": uncertainty if uncertainty is not None else [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }


def _quiet_snapshot() -> dict:
    """A snapshot that triggers zero X-rules across every domain."""

    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "low"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "low"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "low"},
            "today_body_battery": 75,
        },
        "running": {},
    }


@pytest.fixture
def db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection, *proposals: dict) -> None:
    for p in proposals:
        project_proposal(conn, p)


def _table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Snapshot of every synthesis-touched table's row count."""

    counts: dict[str, int] = {}
    for table in (
        "daily_plan",
        "recommendation_log",
        "x_rule_firing",
        "planned_recommendation",
    ):
        counts[table] = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    counts["proposal_log_with_daily_plan_id"] = conn.execute(
        "SELECT COUNT(*) FROM proposal_log WHERE daily_plan_id IS NOT NULL"
    ).fetchone()[0]
    return counts


# ---------------------------------------------------------------------------
# 1. Banned token in proposal-derived rationale → reject
# ---------------------------------------------------------------------------

def test_banned_token_in_proposal_rationale_rejects_synthesis(db):
    _seed(db, _make_proposal(
        "recovery", rationale=["user shows signs of disease today"],
    ))
    pre = _table_counts(db)

    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER, snapshot=_quiet_snapshot(),
        )
    assert "no_banned_tokens" in str(exc_info.value)

    # Atomic rollback: not a single row landed.
    assert _table_counts(db) == pre


def test_banned_token_in_proposal_action_detail_rejects(db):
    _seed(db, _make_proposal(
        "running",
        action="proceed_with_planned_run",
        action_detail={"caveat": "monitor for illness symptoms"},
    ))
    pre = _table_counts(db)

    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER, snapshot=_quiet_snapshot(),
        )
    assert "no_banned_tokens" in str(exc_info.value)
    assert _table_counts(db) == pre


def test_banned_token_in_proposal_uncertainty_rejects(db):
    _seed(db, _make_proposal(
        "sleep",
        action="maintain_schedule",
        uncertainty=["possible_disorder_present"],
    ))
    pre = _table_counts(db)

    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER, snapshot=_quiet_snapshot(),
        )
    assert "no_banned_tokens" in str(exc_info.value)
    assert _table_counts(db) == pre


# ---------------------------------------------------------------------------
# 2-3. Skill draft overlay banned tokens → reject
# ---------------------------------------------------------------------------

def _rec_id(domain: str) -> str:
    """The deterministic recommendation_id _mechanical_draft generates
    for a canonical (non-superseded) plan. Skill drafts must key by this."""
    return f"rec_{FOR_DATE.isoformat()}_{USER}_{domain}_01"


def test_banned_token_in_skill_overlay_rationale_rejects(db):
    _seed(db, _make_proposal("recovery"))
    pre = _table_counts(db)

    skill_drafts = [{
        "recommendation_id": _rec_id("recovery"),
        "rationale": ["agent suspects underlying condition"],
    }]
    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(), skill_drafts=skill_drafts,
        )
    assert "no_banned_tokens" in str(exc_info.value)
    assert _table_counts(db) == pre


def test_banned_token_in_skill_overlay_uncertainty_rejects(db):
    _seed(db, _make_proposal("strength"))
    pre = _table_counts(db)

    skill_drafts = [{
        "recommendation_id": _rec_id("strength"),
        "uncertainty": ["possible_chronic_disease_indicator"],
    }]
    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(), skill_drafts=skill_drafts,
        )
    assert "no_banned_tokens" in str(exc_info.value)
    assert _table_counts(db) == pre


def test_banned_token_in_skill_overlay_review_question_rejects(db):
    _seed(db, _make_proposal("running"))
    pre = _table_counts(db)

    skill_drafts = [{
        "recommendation_id": _rec_id("running"),
        "follow_up": {"review_question": "Did you feel sick during the run?"},
    }]
    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(), skill_drafts=skill_drafts,
        )
    assert "no_banned_tokens" in str(exc_info.value)
    assert _table_counts(db) == pre


# ---------------------------------------------------------------------------
# 4. Atomic rollback — failed synthesis touches NOTHING
# ---------------------------------------------------------------------------

def test_atomic_rollback_leaves_all_synthesis_tables_unchanged(db):
    """End-to-end rollback guarantee. Seed multiple proposals so a
    successful synthesis would touch many tables; force a validation
    failure on one and confirm not a single row landed in any of the
    five synthesis-affected tables."""

    _seed(
        db,
        _make_proposal("recovery"),  # clean
        _make_proposal("sleep"),  # clean
        _make_proposal(
            "running",
            rationale=["clean", "but this one mentions an infection"],
        ),
    )
    pre = _table_counts(db)
    assert pre["proposal_log_with_daily_plan_id"] == 0  # baseline

    with pytest.raises(SynthesisError):
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER, snapshot=_quiet_snapshot(),
        )

    post = _table_counts(db)
    assert post == pre, (
        f"safety failure leaked DB writes: pre={pre}, post={post}"
    )


# ---------------------------------------------------------------------------
# 5. All six domains pass valid recommendation validation
# ---------------------------------------------------------------------------

def test_all_six_domains_synthesize_cleanly_with_valid_proposals(db):
    """Smoke test: the validator dispatches per-domain (recovery /
    running / sleep / strength / stress / nutrition); each must accept
    a valid clean proposal end-to-end through synthesis."""

    _seed(
        db,
        _make_proposal("recovery"),
        _make_proposal("running"),
        _make_proposal("sleep"),
        _make_proposal("strength"),
        _make_proposal("stress"),
        _make_proposal("nutrition"),
    )

    result = run_synthesis(
        db, for_date=FOR_DATE, user_id=USER, snapshot=_quiet_snapshot(),
    )
    # Exactly six final recommendations land.
    assert len(result.recommendation_ids) == 6
    domains = {
        r["domain"]
        for r in [
            json.loads(row["payload_json"])
            for row in db.execute(
                "SELECT payload_json FROM recommendation_log "
                "WHERE for_date = ? AND user_id = ?",
                (FOR_DATE.isoformat(), USER),
            ).fetchall()
        ]
    }
    assert domains == {
        "recovery", "running", "sleep", "strength", "stress", "nutrition",
    }


def test_validator_rejects_recommendation_with_wrong_schema_version_for_domain():
    """Per-domain schema_version dispatch: a running recommendation
    carrying recovery's schema_version is rejected with invariant
    `schema_version`. Belt-and-suspenders for the agent footgun Dom hit
    earlier in the dogfood session."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "training_recommendation.v1",  # wrong for running
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["clean"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "How did the run feel?",
        },
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "schema_version"


def test_validator_rejects_recommendation_with_wrong_action_for_domain():
    """Sleep schema with a recovery-only action is rejected."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "sleep_recommendation.v1",
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "sleep",
        "action": "downgrade_hard_session_to_zone_2",  # recovery action; not valid for sleep
        "action_detail": None,
        "rationale": ["clean"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "Did the schedule hold?",
        },
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "action_enum"


def test_validator_banned_token_in_uncertainty_field_only():
    """Direct unit test on the validator: even when rationale is clean,
    a banned token in `uncertainty` alone must trip the gate (regression
    guard for the v0.1.4 surface expansion)."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "sleep_recommendation.v1",
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "sleep",
        "action": "maintain_schedule",
        "action_detail": None,
        "rationale": ["sleep_status=adequate"],
        "confidence": "moderate",
        "uncertainty": ["possible_sleep_disorder_indicator"],  # banned
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "Did sticking with the schedule feel right?",
        },
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "no_banned_tokens"


def test_validator_banned_token_in_review_question_only():
    """Banned token only in follow_up.review_question must reject."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "stress_recommendation.v1",
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "stress",
        "action": "maintain_routine",
        "action_detail": None,
        "rationale": ["stress_state=manageable"],
        "confidence": "moderate",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "Did anything related to your underlying disease bother you?",
        },
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "no_banned_tokens"


# ---------------------------------------------------------------------------
# Codex 2026-04-24 review pushback: banned tokens in policy_decisions[].note
# ---------------------------------------------------------------------------

def test_validator_banned_token_in_policy_decision_note():
    """Banned token in a policy_decisions[].note must reject. Codex flagged
    that runtime-authored notes still need the sweep — a future code bug
    that leaks a banned token into a decision note shouldn't ship."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "running_recommendation.v1",
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["running_readiness_status=ready"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "How did the run feel?",
        },
        "policy_decisions": [{
            "rule_id": "r1",
            "decision": "allow",
            "note": "user disclosed possible chronic disease in prior intake",
        }],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "no_banned_tokens"


def test_validator_banned_token_recursed_into_nested_action_detail():
    """action_detail can be arbitrarily nested per domain. The recursive
    flattener must catch banned tokens at any depth."""

    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    rec = {
        "schema_version": "running_recommendation.v1",
        "recommendation_id": "rec_x",
        "user_id": "u",
        "issued_at": "2026-04-24T10:00:00+00:00",
        "for_date": "2026-04-24",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": {
            "context": {
                "notes": ["fine on its own", "buried diagnosis token here"],
            },
        },
        "rationale": ["running_readiness_status=ready"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-25T08:00:00+00:00",
            "review_event_id": "rev_x",
            "review_question": "How did the run feel?",
        },
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }

    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(rec)
    assert exc_info.value.invariant == "no_banned_tokens"


# ---------------------------------------------------------------------------
# Codex 2026-04-24 review pushback: banned tokens in proposals
# ---------------------------------------------------------------------------

def test_propose_rejects_banned_token_in_proposal_rationale():
    """Phase A widened: banned tokens must be caught at the proposal seam,
    not only at the recommendation seam. validate_proposal_dict now sweeps
    rationale + action_detail + uncertainty + policy_decisions[].note."""

    from health_agent_infra.core.writeback.proposal import (
        ProposalValidationError,
        validate_proposal_dict,
    )

    proposal = _make_proposal(
        "running",
        rationale=["agent suspects underlying disease"],
    )
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(proposal, expected_domain="running")
    assert exc_info.value.invariant == "no_banned_tokens"


def test_propose_rejects_banned_token_in_proposal_policy_decision_note():
    from health_agent_infra.core.writeback.proposal import (
        ProposalValidationError,
        validate_proposal_dict,
    )

    proposal = _make_proposal("recovery")
    proposal["policy_decisions"] = [{
        "rule_id": "r1",
        "decision": "allow",
        "note": "user reports possible chronic illness symptoms",
    }]
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(proposal, expected_domain="recovery")
    assert exc_info.value.invariant == "no_banned_tokens"


def test_propose_rejects_banned_token_in_nested_action_detail():
    from health_agent_infra.core.writeback.proposal import (
        ProposalValidationError,
        validate_proposal_dict,
    )

    proposal = _make_proposal(
        "stress",
        action_detail={"reason": {"detail": "underlying condition flag"}},
    )
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(proposal, expected_domain="stress")
    assert exc_info.value.invariant == "no_banned_tokens"


