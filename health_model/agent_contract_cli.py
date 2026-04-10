from __future__ import annotations

import argparse
import json
import sys
from typing import Any


CONTRACT_ID = "health_lab_agent_contract"
CONTRACT_VERSION = "2026-04-10"
SHARED_ARGS = {
    "bundle_path": {
        "flag": "--bundle-path",
        "type": "string",
        "required": True,
        "description": "Path to the persisted shared input bundle JSON.",
    },
    "output_dir": {
        "flag": "--output-dir",
        "type": "string",
        "required": True,
        "description": "Directory where generated daily context artifacts are written.",
    },
    "user_id": {
        "flag": "--user-id",
        "type": "string",
        "required": True,
        "description": "Scoped Health Lab user identifier.",
    },
    "date": {
        "flag": "--date",
        "type": "date",
        "required": True,
        "description": "ISO date for the requested daily scope, YYYY-MM-DD.",
    },
    "collected_at": {
        "flag": "--collected-at",
        "type": "datetime",
        "required": True,
        "description": "ISO 8601 timestamp for when the source data was collected.",
    },
    "ingested_at": {
        "flag": "--ingested-at",
        "type": "datetime",
        "required": True,
        "description": "ISO 8601 timestamp for when Health Lab ingested the source data.",
    },
    "raw_location": {
        "flag": "--raw-location",
        "type": "string",
        "required": True,
        "description": "Stable raw-location reference for the input record.",
    },
    "confidence_score": {
        "flag": "--confidence-score",
        "type": "float",
        "required": True,
        "description": "Confidence score in the closed interval [0.0, 1.0].",
    },
    "completeness_state": {
        "flag": "--completeness-state",
        "type": "enum",
        "required": True,
        "accepted_values": ["partial", "complete", "corrected"],
        "description": "Completeness marker for the submitted manual entry.",
    },
    "source_name": {
        "flag": "--source-name",
        "type": "string",
        "required": False,
        "description": "Optional source name override for manual submissions.",
    },
}


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Describe the stable Health Lab external agent contract as machine-readable JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("describe")
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
    if args.command != "describe":
        raise ValueError(f"Unsupported command: {args.command}")

    return {
        "ok": True,
        "contract": _contract_payload(),
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _contract_payload() -> dict[str, Any]:
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "discovery": {
            "cli_module": "health_model.agent_contract_cli",
            "command": "describe",
            "read_only": True,
        },
        "supported_operations": {
            "contract.describe": {
                "module": "health_model.agent_contract_cli",
                "command": "describe",
                "mode": "read",
                "description": "Return this contract description as machine-readable JSON.",
                "args": [],
            },
            "submit.hydration": {
                "module": "health_model.agent_submit_cli",
                "command": "hydration",
                "mode": "write",
                "description": "Append one same-day hydration log and regenerate daily context artifacts.",
                "args": [
                    *(_shared_arg(name) for name in (
                        "bundle_path",
                        "output_dir",
                        "user_id",
                        "date",
                        "collected_at",
                        "ingested_at",
                        "raw_location",
                        "confidence_score",
                        "completeness_state",
                        "source_name",
                    )),
                    {
                        "name": "amount_ml",
                        "flag": "--amount-ml",
                        "type": "float",
                        "required": True,
                        "description": "Hydration amount in millilitres.",
                    },
                    {
                        "name": "beverage_type",
                        "flag": "--beverage-type",
                        "type": "string",
                        "required": False,
                        "description": "Optional beverage type label, for example water.",
                    },
                    {
                        "name": "notes",
                        "flag": "--notes",
                        "type": "string",
                        "required": False,
                        "description": "Optional free-text note.",
                    },
                ],
            },
            "submit.meal": {
                "module": "health_model.agent_submit_cli",
                "command": "meal",
                "mode": "write",
                "description": "Append one same-day meal note and regenerate daily context artifacts.",
                "args": [
                    *(_shared_arg(name) for name in (
                        "bundle_path",
                        "output_dir",
                        "user_id",
                        "date",
                        "collected_at",
                        "ingested_at",
                        "raw_location",
                        "confidence_score",
                        "completeness_state",
                        "source_name",
                    )),
                    {
                        "name": "note_text",
                        "flag": "--note-text",
                        "type": "string",
                        "required": True,
                        "description": "Free-text meal note.",
                    },
                    {
                        "name": "meal_label",
                        "flag": "--meal-label",
                        "type": "string",
                        "required": False,
                        "description": "Optional meal label, for example breakfast, lunch, or dinner.",
                    },
                    {
                        "name": "estimated",
                        "flag": "--estimated",
                        "type": "enum",
                        "required": True,
                        "accepted_values": ["true", "false"],
                        "description": "Whether the meal note is estimated.",
                    },
                    {
                        "name": "notes",
                        "flag": "--notes",
                        "type": "string",
                        "required": False,
                        "description": "Optional free-text note.",
                    },
                ],
            },
            "context.get": {
                "module": "health_model.agent_context_cli",
                "command": "get",
                "mode": "read",
                "description": "Read one dated agent-readable daily context artifact.",
                "args": [
                    {
                        "name": "artifact_path",
                        "flag": "--artifact-path",
                        "type": "string",
                        "required": True,
                        "description": "Path to an agent_readable_daily_context JSON artifact.",
                    },
                    {
                        "name": "user_id",
                        "flag": "--user-id",
                        "type": "string",
                        "required": True,
                        "description": "Scoped Health Lab user identifier.",
                    },
                    {
                        "name": "date",
                        "flag": "--date",
                        "type": "date",
                        "required": True,
                        "description": "ISO date expected inside the artifact, YYYY-MM-DD.",
                    },
                ],
            },
            "context.get_latest": {
                "module": "health_model.agent_context_cli",
                "command": "get-latest",
                "mode": "read",
                "description": "Read the latest agent-readable daily context artifact scoped to one user.",
                "args": [
                    {
                        "name": "artifact_path",
                        "flag": "--artifact-path",
                        "type": "string",
                        "required": True,
                        "description": "Path to the latest agent_readable_daily_context JSON artifact.",
                    },
                    {
                        "name": "user_id",
                        "flag": "--user-id",
                        "type": "string",
                        "required": True,
                        "description": "Scoped Health Lab user identifier.",
                    },
                ],
            },
        },
        "accepted_enums": {
            "submit_commands": ["hydration", "meal"],
            "context_commands": ["get", "get-latest"],
            "contract_commands": ["describe"],
            "completeness_state": ["partial", "complete", "corrected"],
            "estimated": ["true", "false"],
        },
        "artifact_types": {
            "consumed": [
                {
                    "artifact_type": "shared_input_bundle",
                    "shape": "persisted shared-input bundle JSON consumed through --bundle-path",
                },
                {
                    "artifact_type": "agent_readable_daily_context",
                    "shape": "read-only context JSON consumed through --artifact-path",
                },
            ],
            "produced": [
                {
                    "artifact_type": "agent_readable_daily_context",
                    "paths": [
                        "{output_dir}/agent_readable_daily_context_{date}.json",
                        "{output_dir}/agent_readable_daily_context_latest.json",
                    ],
                }
            ],
        },
        "path_conventions": {
            "bundle_path": "{output_dir}/shared_input_bundle_{date}.json",
            "dated_context_artifact": "{output_dir}/agent_readable_daily_context_{date}.json",
            "latest_context_artifact": "{output_dir}/agent_readable_daily_context_latest.json",
        },
        "response_envelopes": {
            "contract.describe": {
                "success_keys": ["ok", "contract", "validation", "error"],
                "error_keys": ["ok", "contract", "validation", "error"],
            },
            "submit": {
                "success_keys": ["ok", "bundle_path", "dated_artifact_path", "latest_artifact_path", "accepted_provenance", "validation", "error"],
                "error_keys": ["ok", "bundle_path", "dated_artifact_path", "latest_artifact_path", "accepted_provenance", "validation", "error"],
            },
            "context": {
                "success_keys": ["ok", "artifact_path", "context", "validation", "error"],
                "error_keys": ["ok", "artifact_path", "context", "validation", "error"],
            },
        },
    }


def _shared_arg(name: str) -> dict[str, Any]:
    return {"name": name, **SHARED_ARGS[name]}


def _error_response(
    *,
    code: str,
    message: str,
    args: argparse.Namespace | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "contract": None,
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


if __name__ == "__main__":
    raise SystemExit(main())
