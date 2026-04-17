"""`hai` CLI — thin subcommands over the deterministic runtime.

Subcommands:

    hai pull      — acquire Garmin evidence for a date, emit JSON
    hai clean     — normalize evidence into CleanedEvidence + RawSummary JSON
    hai writeback — schema-validate a recommendation JSON and persist
    hai review    — schedule review events, record outcomes, summarize history
    hai setup-skills — copy the packaged skills/ directory to ~/.claude/skills/

All judgment (state classification, policy, recommendation shaping) lives in
the markdown skills shipped with this package. This CLI is a tooling surface
for an agent to call; it does not reason about evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from health_agent_infra.clean import build_raw_summary, clean_inputs
from health_agent_infra.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    default_manual_readiness,
)
from health_agent_infra.review.outcomes import (
    record_review_outcome,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.schemas import (
    FollowUp,
    PolicyDecision,
    ReviewEvent,
    ReviewOutcome,
    TrainingRecommendation,
)
from health_agent_infra.validate import (
    RecommendationValidationError,
    validate_recommendation_dict,
)
from health_agent_infra.writeback.recommendation import perform_writeback


PACKAGE_ROOT = Path(__file__).resolve().parent
SKILLS_SOURCE = PACKAGE_ROOT.parent.parent / "skills"
DEFAULT_CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _coerce_date(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(value)


def _coerce_dt(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _emit_json(obj: Any) -> None:
    def default(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"not serializable: {type(o).__name__}")

    print(json.dumps(obj, default=default, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# hai pull
# ---------------------------------------------------------------------------

def cmd_pull(args: argparse.Namespace) -> int:
    as_of = _coerce_date(args.date)
    adapter = GarminRecoveryReadinessAdapter()
    pull = adapter.load(as_of)

    manual = None
    if args.manual_readiness_json:
        manual = json.loads(Path(args.manual_readiness_json).read_text(encoding="utf-8"))
    elif args.use_default_manual_readiness:
        manual = default_manual_readiness(as_of)

    payload = {
        "as_of_date": as_of.isoformat(),
        "user_id": args.user_id,
        "source": adapter.source_name,
        "pull": pull,
        "manual_readiness": manual,
    }
    _emit_json(payload)
    return 0


# ---------------------------------------------------------------------------
# hai clean
# ---------------------------------------------------------------------------

def cmd_clean(args: argparse.Namespace) -> int:
    pulled = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    as_of = _coerce_date(pulled["as_of_date"])
    user_id = pulled["user_id"]
    pull = pulled["pull"]
    manual = pulled.get("manual_readiness")

    evidence = clean_inputs(
        user_id=user_id,
        as_of_date=as_of,
        garmin_sleep=pull.get("sleep"),
        garmin_resting_hr_recent=pull.get("resting_hr", []),
        garmin_hrv_recent=pull.get("hrv", []),
        garmin_training_load_7d=pull.get("training_load", []),
        manual_readiness=manual,
    )
    summary = build_raw_summary(
        user_id=user_id,
        as_of_date=as_of,
        garmin_sleep=pull.get("sleep"),
        garmin_resting_hr_recent=pull.get("resting_hr", []),
        garmin_hrv_recent=pull.get("hrv", []),
        garmin_training_load_7d=pull.get("training_load", []),
    )
    _emit_json({
        "cleaned_evidence": evidence.to_dict(),
        "raw_summary": summary.to_dict(),
    })
    return 0


# ---------------------------------------------------------------------------
# hai writeback — schema-validated recommendation persistence
# ---------------------------------------------------------------------------

def _recommendation_from_dict(data: dict) -> TrainingRecommendation:
    """Construct a TrainingRecommendation from agent-produced JSON.

    Calls ``validate_recommendation_dict`` first — that pure function owns
    every code-enforced invariant. This function is straight deserialization
    after the validator has accepted the input; it carries no policy checks
    of its own.
    """

    validate_recommendation_dict(data)

    follow_up_data = data["follow_up"]
    follow_up = FollowUp(
        review_at=_coerce_dt(follow_up_data["review_at"]),
        review_question=follow_up_data["review_question"],
        review_event_id=follow_up_data["review_event_id"],
    )
    policy_decisions = [
        PolicyDecision(rule_id=d["rule_id"], decision=d["decision"], note=d["note"])
        for d in data["policy_decisions"]
    ]
    return TrainingRecommendation(
        schema_version=data["schema_version"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        issued_at=_coerce_dt(data["issued_at"]),
        for_date=date.fromisoformat(data["for_date"]),
        action=data["action"],
        action_detail=data.get("action_detail"),
        rationale=list(data["rationale"]),
        confidence=data["confidence"],
        uncertainty=list(data["uncertainty"]),
        follow_up=follow_up,
        policy_decisions=policy_decisions,
        bounded=data["bounded"],
    )


def cmd_writeback(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    try:
        recommendation = _recommendation_from_dict(data)
    except RecommendationValidationError as exc:
        print(
            f"writeback rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return 2
    except (ValueError, KeyError) as exc:
        print(f"writeback rejected: {exc}", file=sys.stderr)
        return 2
    record = perform_writeback(recommendation, base_dir=Path(args.base_dir))
    _emit_json(record.to_dict())
    return 0


# ---------------------------------------------------------------------------
# hai review
# ---------------------------------------------------------------------------

def cmd_review_schedule(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    recommendation = _recommendation_from_dict(data)
    event = schedule_review(recommendation, base_dir=Path(args.base_dir))
    _emit_json(event.to_dict())
    return 0


def cmd_review_record(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.outcome_json).read_text(encoding="utf-8"))
    event = ReviewEvent(
        review_event_id=data["review_event_id"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        review_at=_coerce_dt(data.get("review_at", datetime.now(timezone.utc).isoformat())),
        review_question=data.get("review_question", ""),
    )
    outcome = record_review_outcome(
        event,
        base_dir=Path(args.base_dir),
        followed_recommendation=data["followed_recommendation"],
        self_reported_improvement=data.get("self_reported_improvement"),
        free_text=data.get("free_text"),
        now=_coerce_dt(data.get("recorded_at")),
    )
    _emit_json(outcome.to_dict())
    return 0


def cmd_review_summary(args: argparse.Namespace) -> int:
    outcomes_path = Path(args.base_dir) / "review_outcomes.jsonl"
    if not outcomes_path.exists():
        _emit_json(summarize_review_history([]))
        return 0
    outcomes: list[ReviewOutcome] = []
    for line in outcomes_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if args.user_id and d.get("user_id") != args.user_id:
            continue
        outcomes.append(ReviewOutcome(
            review_event_id=d["review_event_id"],
            recommendation_id=d["recommendation_id"],
            user_id=d["user_id"],
            recorded_at=_coerce_dt(d["recorded_at"]),
            followed_recommendation=d["followed_recommendation"],
            self_reported_improvement=d.get("self_reported_improvement"),
            free_text=d.get("free_text"),
        ))
    _emit_json(summarize_review_history(outcomes))
    return 0


# ---------------------------------------------------------------------------
# hai intake readiness — typed manual readiness intake, emits JSON to stdout
# ---------------------------------------------------------------------------

SORENESS_CHOICES = ("low", "moderate", "high")
ENERGY_CHOICES = ("low", "moderate", "high")


def cmd_intake_readiness(args: argparse.Namespace) -> int:
    """Emit a typed manual-readiness JSON blob to stdout.

    Composes with ``hai pull --manual-readiness-json <path>`` so an agent can
    capture structured readiness without hand-authoring JSON.
    """

    as_of = _coerce_date(args.as_of)
    # Microsecond timestamp in the submission_id keeps it unique across
    # rapid same-day re-invocations without pulling in uuid.
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    payload: dict[str, Any] = {
        "submission_id": f"m_ready_{as_of.isoformat()}_{suffix}",
        "soreness": args.soreness,
        "energy": args.energy,
        "planned_session_type": args.planned_session_type,
    }
    if args.active_goal:
        payload["active_goal"] = args.active_goal
    _emit_json(payload)
    return 0


# ---------------------------------------------------------------------------
# hai setup-skills
# ---------------------------------------------------------------------------

def cmd_setup_skills(args: argparse.Namespace) -> int:
    if not SKILLS_SOURCE.exists():
        print(f"skills/ not found at {SKILLS_SOURCE}", file=sys.stderr)
        return 2
    dest = Path(args.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for skill_dir in SKILLS_SOURCE.iterdir():
        if not skill_dir.is_dir():
            continue
        target = dest / skill_dir.name
        if target.exists():
            if not args.force:
                print(f"skipping existing skill: {target} (pass --force to overwrite)")
                continue
            shutil.rmtree(target)
        shutil.copytree(skill_dir, target)
        copied.append(str(target))
    _emit_json({"copied": copied, "dest": str(dest)})
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hai", description="Health Agent Infra CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pull = sub.add_parser("pull", help="Pull Garmin evidence for a date")
    p_pull.add_argument("--date", default=None, help="As-of date, ISO-8601 (default today UTC)")
    p_pull.add_argument("--user-id", default="u_local_1")
    p_pull.add_argument("--manual-readiness-json", default=None,
                        help="Path to a JSON file with manual readiness fields")
    p_pull.add_argument("--use-default-manual-readiness", action="store_true",
                        help="Use a neutral manual readiness default (for offline runs)")
    p_pull.set_defaults(func=cmd_pull)

    p_clean = sub.add_parser("clean", help="Normalize pulled evidence + raw summary")
    p_clean.add_argument("--evidence-json", required=True,
                         help="Path to a JSON file produced by `hai pull`")
    p_clean.set_defaults(func=cmd_clean)

    p_wb = sub.add_parser("writeback", help="Schema-validate and persist a recommendation")
    p_wb.add_argument("--recommendation-json", required=True,
                      help="Path to a JSON file matching TrainingRecommendation")
    p_wb.add_argument("--base-dir", required=True,
                      help="Writeback root (must contain 'recovery_readiness_v1')")
    p_wb.set_defaults(func=cmd_writeback)

    p_review = sub.add_parser("review", help="Review scheduling + outcome persistence")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_rs = review_sub.add_parser("schedule", help="Persist a pending review event for a recommendation")
    p_rs.add_argument("--recommendation-json", required=True)
    p_rs.add_argument("--base-dir", required=True)
    p_rs.set_defaults(func=cmd_review_schedule)

    p_rr = review_sub.add_parser("record", help="Record a review outcome")
    p_rr.add_argument("--outcome-json", required=True)
    p_rr.add_argument("--base-dir", required=True)
    p_rr.set_defaults(func=cmd_review_record)

    p_rsum = review_sub.add_parser("summary", help="Summarize outcome history counts")
    p_rsum.add_argument("--base-dir", required=True)
    p_rsum.add_argument("--user-id", default=None)
    p_rsum.set_defaults(func=cmd_review_summary)

    p_intake = sub.add_parser("intake", help="Typed human-input intake surfaces")
    intake_sub = p_intake.add_subparsers(dest="intake_command", required=True)
    p_ir = intake_sub.add_parser("readiness",
                                 help="Emit a typed manual-readiness JSON to stdout")
    p_ir.add_argument("--soreness", required=True, choices=SORENESS_CHOICES,
                      help="Subjective soreness band: low | moderate | high")
    p_ir.add_argument("--energy", required=True, choices=ENERGY_CHOICES,
                      help="Subjective energy band: low | moderate | high")
    p_ir.add_argument("--planned-session-type", required=True,
                      help="Planned session type (free text; e.g. easy, moderate, hard, intervals, race, rest)")
    p_ir.add_argument("--active-goal", default=None,
                      help="Optional active training goal (free text)")
    p_ir.add_argument("--as-of", default=None,
                      help="As-of date for submission_id (ISO-8601, default today UTC)")
    p_ir.set_defaults(func=cmd_intake_readiness)

    p_setup = sub.add_parser("setup-skills", help="Copy packaged skills/ into ~/.claude/skills/")
    p_setup.add_argument("--dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR))
    p_setup.add_argument("--force", action="store_true",
                         help="Overwrite existing skill directories of the same name")
    p_setup.set_defaults(func=cmd_setup_skills)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
