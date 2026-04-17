"""REVIEW layer.

Schedules the next-day review event for an emitted recommendation, and records
the review outcome once the user provides a response. Review outcomes are
appended to a local JSONL and linked to the originating recommendation via
recommendation_id.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from health_agent_infra.schemas import (
    ReviewEvent,
    ReviewOutcome,
    TrainingRecommendation,
)


def schedule_review(
    recommendation: TrainingRecommendation,
    *,
    base_dir: Path,
) -> ReviewEvent:
    """Persist a pending review event for the given recommendation."""

    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    events_path = base_dir / "review_events.jsonl"

    event = ReviewEvent(
        review_event_id=recommendation.follow_up.review_event_id,
        recommendation_id=recommendation.recommendation_id,
        user_id=recommendation.user_id,
        review_at=recommendation.follow_up.review_at,
        review_question=recommendation.follow_up.review_question,
    )

    if not _event_already_written(events_path, event.review_event_id):
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
    return event


def record_review_outcome(
    event: ReviewEvent,
    *,
    base_dir: Path,
    followed_recommendation: bool,
    self_reported_improvement: Optional[bool],
    free_text: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ReviewOutcome:
    """Persist a user-supplied outcome for a previously scheduled review event."""

    now = now or datetime.now(timezone.utc)
    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = base_dir / "review_outcomes.jsonl"

    outcome = ReviewOutcome(
        review_event_id=event.review_event_id,
        recommendation_id=event.recommendation_id,
        user_id=event.user_id,
        recorded_at=now,
        followed_recommendation=followed_recommendation,
        self_reported_improvement=self_reported_improvement,
        free_text=free_text,
    )

    with outcomes_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")
    return outcome


def _event_already_written(path: Path, review_event_id: str) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("review_event_id") == review_event_id:
                return True
    return False


def summarize_review_history(outcomes: list[ReviewOutcome]) -> dict[str, int]:
    """Count review outcomes by category. Deterministic bookkeeping, not judgment.

    The runtime surfaces structured summary state; the LLM consumer forms
    its own view about what the numbers mean for future recommendation
    confidence. This function does not encode any opinion about how good
    or bad a given outcome distribution is.

    Returned keys (all non-negative integers, always present):
      - ``total``: total number of outcomes in the input.
      - ``followed_improved``: followed recommendation AND self-reported
        improvement was ``True``.
      - ``followed_no_change``: followed recommendation AND self-reported
        improvement was ``False``.
      - ``followed_unknown``: followed recommendation AND self-reported
        improvement was ``None`` (ambiguous).
      - ``not_followed``: did not follow the recommendation (improvement
        field ignored — no counterfactual).

    The four non-total keys always sum to ``total``; a consumer can derive
    any rate it wants from these counts without the runtime taking a
    position on which rate matters.
    """

    summary = {
        "total": len(outcomes),
        "followed_improved": 0,
        "followed_no_change": 0,
        "followed_unknown": 0,
        "not_followed": 0,
    }

    for outcome in outcomes:
        if not outcome.followed_recommendation:
            summary["not_followed"] += 1
            continue
        if outcome.self_reported_improvement is True:
            summary["followed_improved"] += 1
        elif outcome.self_reported_improvement is False:
            summary["followed_no_change"] += 1
        else:
            summary["followed_unknown"] += 1

    return summary
