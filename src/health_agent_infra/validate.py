"""Pure validators for agent-produced JSON.

The validator is the runtime's code-enforced boundary on the agent's output.
Skills describe how the agent should reason; this module enforces the
invariants the runtime must guarantee regardless of skill drift or prompt
manipulation.

Every invariant has a stable machine-readable id so tests and callers can
pattern-match on the specific violation rather than parsing prose.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from health_agent_infra.schemas import RECOMMENDATION_SCHEMA_VERSION


ALLOWED_ACTIONS: frozenset[str] = frozenset({
    "proceed_with_planned_session",
    "downgrade_hard_session_to_zone_2",
    "downgrade_session_to_mobility_only",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
})

ALLOWED_CONFIDENCE: frozenset[str] = frozenset({"low", "moderate", "high"})

# R2 — diagnosis-shaped tokens. Lower-case; matching is case-insensitive.
BANNED_TOKENS: frozenset[str] = frozenset({
    "diagnosis",
    "diagnose",
    "diagnosed",
    "syndrome",
    "disease",
    "disorder",
    "condition",
    "infection",
    "illness",
    "sick",
})

FOLLOW_UP_WINDOW = timedelta(hours=24)


REQUIRED_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "recommendation_id",
    "user_id",
    "issued_at",
    "for_date",
    "action",
    "rationale",
    "confidence",
    "uncertainty",
    "follow_up",
    "policy_decisions",
    "bounded",
})


class RecommendationValidationError(ValueError):
    """Raised when a recommendation dict violates a code-enforced invariant.

    The ``invariant`` attribute carries a stable machine-readable id so tests
    and `hai writeback` can pattern-match on the specific violation.
    """

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def validate_recommendation_dict(data: Any) -> None:
    """Validate an agent-produced recommendation dict.

    Raises ``RecommendationValidationError`` on the first violation, with
    ``.invariant`` set to the stable id of the invariant that failed.
    Returns ``None`` on success.

    Invariant ids (stable, machine-readable):
      - required_fields_present
      - schema_version
      - action_enum
      - confidence_enum
      - bounded_true
      - no_banned_tokens
      - follow_up_shape
      - review_at_within_24h
      - policy_decisions_present
    """

    if not isinstance(data, dict):
        raise RecommendationValidationError(
            "required_fields_present",
            f"expected dict, got {type(data).__name__}",
        )

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise RecommendationValidationError(
            "required_fields_present",
            f"missing required fields: {sorted(missing)}",
        )

    if data["schema_version"] != RECOMMENDATION_SCHEMA_VERSION:
        raise RecommendationValidationError(
            "schema_version",
            f"expected {RECOMMENDATION_SCHEMA_VERSION!r}, got {data['schema_version']!r}",
        )

    action = data["action"]
    if action not in ALLOWED_ACTIONS:
        raise RecommendationValidationError(
            "action_enum",
            f"action {action!r} not in allowed set {sorted(ALLOWED_ACTIONS)}",
        )

    confidence = data["confidence"]
    if confidence not in ALLOWED_CONFIDENCE:
        raise RecommendationValidationError(
            "confidence_enum",
            f"confidence {confidence!r} not in {sorted(ALLOWED_CONFIDENCE)}",
        )

    if data["bounded"] is not True:
        raise RecommendationValidationError(
            "bounded_true",
            f"bounded must be True, got {data['bounded']!r}",
        )

    # R2 — banned tokens in rationale strings and action_detail values.
    _check_banned_tokens(data)

    follow_up = data.get("follow_up")
    if not isinstance(follow_up, dict):
        raise RecommendationValidationError(
            "follow_up_shape",
            f"follow_up must be an object, got {type(follow_up).__name__}",
        )
    for fu_field in ("review_at", "review_question", "review_event_id"):
        if fu_field not in follow_up:
            raise RecommendationValidationError(
                "follow_up_shape",
                f"follow_up missing {fu_field!r}",
            )

    # R4 — review_at within 24h of issued_at.
    try:
        issued_at = _parse_dt(data["issued_at"])
        review_at = _parse_dt(follow_up["review_at"])
    except ValueError as exc:
        raise RecommendationValidationError(
            "review_at_within_24h",
            f"could not parse timestamps: {exc}",
        )
    delta = review_at - issued_at
    if delta < timedelta(0) or delta > FOLLOW_UP_WINDOW:
        raise RecommendationValidationError(
            "review_at_within_24h",
            f"review_at must be within {FOLLOW_UP_WINDOW} of issued_at; "
            f"delta={delta}",
        )

    policy_decisions = data["policy_decisions"]
    if not isinstance(policy_decisions, list) or len(policy_decisions) < 1:
        raise RecommendationValidationError(
            "policy_decisions_present",
            f"policy_decisions must be a non-empty list; got {policy_decisions!r}",
        )


def _check_banned_tokens(data: dict) -> None:
    rationale = data.get("rationale", [])
    parts: list[str] = []
    if isinstance(rationale, list):
        parts.extend(str(r) for r in rationale)
    else:
        parts.append(str(rationale))
    detail = data.get("action_detail")
    if isinstance(detail, dict):
        parts.extend(str(v) for v in detail.values())
    elif detail is not None:
        parts.append(str(detail))

    haystack = " ".join(parts).lower()
    for token in BANNED_TOKENS:
        if token in haystack:
            raise RecommendationValidationError(
                "no_banned_tokens",
                f"banned diagnosis-shaped token {token!r} found in "
                f"rationale or action_detail",
            )


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=None)
    if not isinstance(value, str):
        raise ValueError(f"expected str or datetime, got {type(value).__name__}")
    return datetime.fromisoformat(value)
