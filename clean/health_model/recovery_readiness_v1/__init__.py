"""Compatibility shim for recovery_readiness_v1.

The tooling for the flagship loop has moved to the installable
``health_agent_infra`` package under ``src/health_agent_infra/``.
This shim re-exports the public symbols from the new location so
existing callers (tests, older CLI chain, docs) keep importing from
``health_model.recovery_readiness_v1`` during the repo reshape.

The shim itself is legacy; later commits in the reshape will remove
the ``state.py`` / ``policy.py`` / ``recommend.py`` / ``cli.py`` that
still live alongside this file, and this package directory will be
deleted entirely once the older CLI chain is swept.
"""

from health_agent_infra.schemas import (
    CleanedEvidence,
    PolicyDecision,
    RecoveryState,
    ReviewEvent,
    ReviewOutcome,
    SignalQuality,
    TrainingRecommendation,
)
from health_agent_infra.clean.recovery_prep import clean_inputs
from health_agent_infra.writeback.recommendation import perform_writeback
from health_agent_infra.review.outcomes import (
    record_review_outcome,
    schedule_review,
)
from health_model.recovery_readiness_v1.state import build_recovery_state
from health_model.recovery_readiness_v1.policy import evaluate_policy, POLICY_RULES
from health_model.recovery_readiness_v1.recommend import build_training_recommendation

__all__ = [
    "CleanedEvidence",
    "PolicyDecision",
    "RecoveryState",
    "ReviewEvent",
    "ReviewOutcome",
    "SignalQuality",
    "TrainingRecommendation",
    "clean_inputs",
    "build_recovery_state",
    "evaluate_policy",
    "POLICY_RULES",
    "build_training_recommendation",
    "perform_writeback",
    "schedule_review",
    "record_review_outcome",
]
