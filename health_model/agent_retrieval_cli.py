from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from health_model import agent_context_cli
from health_model.retrieval_request_metadata import validate_and_echo_request_metadata


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


SLEEP_EVIDENCE_KEYS = [
    "primary_sleep_window",
    "total_sleep_duration_minutes",
    "subjective_sleep_quality",
    "sleep_timing_regularity_marker",
    "sleep_disruption_markers",
]
RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE = "recommendation_judgment"
RECOMMENDATION_JUDGMENT_EVIDENCE_KEYS = [
    "judgment_id",
    "judgment_label",
    "action_taken",
    "why",
    "recommendation_artifact_path",
    "recommendation_artifact_id",
    "recommendation_evidence_refs",
    "written_at",
    "request_id",
    "requested_at",
]


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Run bounded Health Lab retrieval operations through a stable JSON CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sleep_review = subparsers.add_parser("sleep-review")
    sleep_review.add_argument("--artifact-path", required=True)
    sleep_review.add_argument("--user-id", required=True)
    sleep_review.add_argument("--date", required=True)
    sleep_review.add_argument("--request-id", required=True)
    sleep_review.add_argument("--requested-at", required=True)
    sleep_review.add_argument("--include-conflicts", choices=["true", "false"])
    sleep_review.add_argument("--include-missingness", choices=["true", "false"])

    recommendation_judgment = subparsers.add_parser("recommendation-judgment")
    recommendation_judgment.add_argument("--artifact-path", required=True)
    recommendation_judgment.add_argument("--user-id", required=True)
    recommendation_judgment.add_argument("--date", required=True)
    recommendation_judgment.add_argument("--request-id", required=True)
    recommendation_judgment.add_argument("--requested-at", required=True)
    recommendation_judgment.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation_judgment.add_argument("--include-missingness", choices=["true", "false"])

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
        response = run_command(args)
    except CliParseError as exc:
        print(json.dumps(_error_response(code="cli_parse_error", message=str(exc), argv=argv), indent=2, sort_keys=True))
        return 1
    except Exception as exc:
        print(
            json.dumps(
                _error_response(
                    code="cli_runtime_error",
                    message=str(exc),
                    args=args if "args" in locals() else None,
                    argv=argv,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") else 1


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "sleep-review":
        return _run_sleep_review(args)
    if args.command == "recommendation-judgment":
        return _run_recommendation_judgment(args)
    raise ValueError(f"Unsupported command: {args.command}")


def _run_sleep_review(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.artifact_path,
            "retrieval": None,
            "validation": request_validation,
            "error": {
                "code": request_validation["semantic_issues"][0]["code"],
                "message": "Request metadata failed validation.",
                "retryable": False,
                "details": {
                    "command": args.command,
                    "request_echo": request_validation["request_echo"],
                },
            },
        }

    context_response = agent_context_cli.run_command(
        argparse.Namespace(
            command="get",
            artifact_path=args.artifact_path,
            user_id=args.user_id,
            date=args.date,
        )
    )
    if not context_response.get("ok"):
        return {
            "ok": False,
            "artifact_path": context_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **context_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": context_response["error"],
        }

    context = context_response["context"]
    sleep_context = context["semantic_context"]["sleep"]
    evidence = {key: sleep_context[key] for key in SLEEP_EVIDENCE_KEYS}
    important_gaps = [gap["code"] for gap in sleep_context.get("important_gaps", [])]
    conflicts = sleep_context.get("conflicts", []) if args.include_conflicts != "false" else []

    return {
        "ok": True,
        "artifact_path": context_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.sleep_review",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": _coverage_status(evidence=evidence, important_gaps=important_gaps),
            "generated_from": context.get("generated_from", {}),
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            **context_response["validation"],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _run_recommendation_judgment(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.artifact_path,
            "retrieval": None,
            "validation": request_validation,
            "error": {
                "code": request_validation["semantic_issues"][0]["code"],
                "message": "Request metadata failed validation.",
                "retryable": False,
                "details": {
                    "command": args.command,
                    "request_echo": request_validation["request_echo"],
                },
            },
        }

    artifact_response = _read_recommendation_judgment_artifact(
        path=Path(args.artifact_path),
        user_id=args.user_id,
        date=args.date,
    )
    if not artifact_response["ok"]:
        return {
            "ok": False,
            "artifact_path": artifact_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **artifact_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": artifact_response["error"],
        }

    artifact = artifact_response["artifact"]
    important_gaps: list[str] = []
    conflicts: list[dict[str, Any]] = [] if args.include_conflicts != "false" else []
    evidence = {key: artifact[key] for key in RECOMMENDATION_JUDGMENT_EVIDENCE_KEYS if key in artifact}

    return {
        "ok": True,
        "artifact_path": artifact_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.recommendation_judgment",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": "present",
            "generated_from": {
                "artifact_path": artifact_response["artifact_path"],
                "recommendation_artifact_path": artifact.get("recommendation_artifact_path"),
                "request_id": artifact.get("request_id"),
            },
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            **artifact_response["validation"],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _read_recommendation_judgment_artifact(*, path: Path, user_id: str, date: str) -> dict[str, Any]:
    if not path.exists():
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="artifact_not_found",
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code="artifact_not_found", message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="invalid_artifact_json",
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code="invalid_artifact_json", message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    semantic_issues = _recommendation_judgment_semantic_issues(raw=raw, user_id=user_id, date=date)
    if semantic_issues:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code=semantic_issues[0]["code"],
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": user_id, "date": date},
        )

    return {
        "ok": True,
        "artifact_path": str(path),
        "artifact": raw,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _recommendation_judgment_semantic_issues(*, raw: Any, user_id: str, date: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="artifact_type_mismatch",
                message=f"Expected artifact_type={RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if raw.get("user_id") != user_id:
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _retrieval_validation_error(
    *,
    artifact_path: str,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "artifact": None,
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": semantic_issues},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details,
        },
    }


def _coverage_status(*, evidence: dict[str, Any], important_gaps: list[str]) -> str:
    statuses = [item.get("status") for item in evidence.values() if isinstance(item, dict)]
    if not statuses or all(status == "missing" for status in statuses):
        return "missing"
    if important_gaps or any(status == "missing" for status in statuses):
        return "partial"
    return "present"


def _error_response(
    *,
    code: str,
    message: str,
    args: argparse.Namespace | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": getattr(args, "artifact_path", None),
        "retrieval": None,
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": []},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": {
                "command": getattr(args, "command", None),
                "argv": argv or sys.argv[1:],
            },
        },
    }


def _issue(*, code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


if __name__ == "__main__":
    raise SystemExit(main())
