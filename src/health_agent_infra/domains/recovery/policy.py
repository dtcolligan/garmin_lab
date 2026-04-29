"""Recovery-domain mechanical policy gates (R1, R5, R6).

Extracted from `skills/recovery-readiness/SKILL.md` (Phase 1 step 3).
These three rules produce deterministic decisions that the skill must
honour; the remaining invariants (R2 banned tokens, R3 action envelope,
R4 review-within-24h) stay in `core/validate.py` as writeback-time
checks.

After calling `classify_recovery_state`, callers pass the result and the
same `raw_summary` to `evaluate_recovery_policy`. The returned
`RecoveryPolicyResult` carries:

- `policy_decisions`: every rule evaluated, with decision tier + note.
- `forced_action`: set when a rule mechanically determines the action
  (R1 → `defer_decision_insufficient_signal`, R6 →
  `escalate_for_user_review`). The skill honours this instead of running
  the action matrix.
- `forced_action_detail`: optional dict of reason tokens / counters for
  the forced action.
- `capped_confidence`: set when a rule enforces a ceiling (R5 →
  `moderate`). The skill applies this after choosing confidence from
  coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.recovery.classify import ClassifiedRecoveryState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class RecoveryPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r1_coverage_gate(
    classified: ClassifiedRecoveryState,
) -> tuple[PolicyDecision, Optional[str]]:
    """R1 require_min_coverage. Returns (decision, forced_action_or_None)."""

    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required inputs missing",
            ),
            "defer_decision_insufficient_signal",
        )

    return (
        PolicyDecision(
            rule_id="require_min_coverage",
            decision="allow",
            note=f"coverage={classified.coverage_band}; required inputs present",
        ),
        None,
    )


def _r5_sparse_confidence_cap(
    classified: ClassifiedRecoveryState,
) -> tuple[PolicyDecision, Optional[str]]:
    """R5 no_high_confidence_on_sparse_signal. Caps at moderate when sparse."""

    if classified.coverage_band == "sparse":
        tokens_str = ",".join(classified.uncertainty) if classified.uncertainty else ""
        return (
            PolicyDecision(
                rule_id="no_high_confidence_on_sparse_signal",
                decision="soften",
                note=f"capped confidence to moderate on sparse signal ({tokens_str})",
            ),
            "moderate",
        )

    return (
        PolicyDecision(
            rule_id="no_high_confidence_on_sparse_signal",
            decision="allow",
            note=f"coverage={classified.coverage_band}; no cap required",
        ),
        None,
    )


def _r6_resting_hr_spike(
    raw_summary: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    """R6 resting_hr_spike_escalation. Escalates when spike days >= threshold."""

    from health_agent_infra.core.config import coerce_int  # noqa: PLC0415

    spike_days = raw_summary.get("resting_hr_spike_days")
    threshold = coerce_int(
        t["policy"]["recovery"]["r6_resting_hr_spike_days_threshold"],
        name="policy.recovery.r6_resting_hr_spike_days_threshold",
    )

    if spike_days is not None and spike_days >= threshold:
        detail = {
            "reason_token": "resting_hr_spike_3_days_running",
            "consecutive_days": spike_days,
        }
        return (
            PolicyDecision(
                rule_id="resting_hr_spike_escalation",
                decision="escalate",
                note=f"resting_hr_spike_days={spike_days} >= threshold={threshold}",
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="resting_hr_spike_escalation",
            decision="allow",
            note=(
                f"resting_hr_spike_days={spike_days} below threshold={threshold}"
                if spike_days is not None
                else "resting_hr_spike_days unavailable; no escalation"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_recovery_policy(
    classified: ClassifiedRecoveryState,
    raw_summary: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> RecoveryPolicyResult:
    """Apply R1, R5, R6 to a classified recovery state.

    Returns every decision (allow / block / soften / escalate) along with
    any forced_action or capped_confidence the skill must honour. Rule
    ordering matches the skill: R1 short-circuits action selection; R6
    overrides even if R1 allows; R5 caps confidence independently of
    action.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    decisions: list[PolicyDecision] = []
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None

    r1_dec, r1_forced = _r1_coverage_gate(classified)
    decisions.append(r1_dec)
    if r1_forced is not None:
        forced_action = r1_forced

    r5_dec, r5_cap = _r5_sparse_confidence_cap(classified)
    decisions.append(r5_dec)
    if r5_cap is not None:
        capped_confidence = r5_cap

    r6_dec, r6_forced, r6_detail = _r6_resting_hr_spike(raw_summary, t)
    decisions.append(r6_dec)
    if r6_forced is not None:
        # R6 overrides R1's defer because it's a louder signal; if R1
        # already blocked we still prefer the escalation.
        forced_action = r6_forced
        forced_action_detail = r6_detail

    return RecoveryPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
    )
