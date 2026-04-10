from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from health_model.agent_readable_daily_context import build_agent_readable_daily_context
from health_model.shared_input_backbone import validate_shared_input_bundle


def build_daily_context_artifact(*, bundle_path: str, user_id: str, date: str, output_dir: str) -> dict[str, Any]:
    bundle_file = Path(bundle_path)
    output_path = Path(output_dir)

    bundle = json.loads(bundle_file.read_text())
    validation = validate_shared_input_bundle(bundle)
    if not validation.is_valid:
        raise BundleValidationFailed(validation)

    artifact = build_agent_readable_daily_context(bundle, user_id=user_id, date=date)

    output_path.mkdir(parents=True, exist_ok=True)
    dated_path = output_path / f"agent_readable_daily_context_{date}.json"
    latest_path = output_path / "agent_readable_daily_context_latest.json"

    serialized = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    dated_path.write_text(serialized)
    latest_path.write_text(serialized)

    return {
        "artifact": artifact,
        "dated_path": str(dated_path),
        "latest_path": str(latest_path),
    }


class BundleValidationFailed(ValueError):
    def __init__(self, validation: Any) -> None:
        self.validation = validation
        super().__init__(self._message())

    def _message(self) -> str:
        issues = [
            *(f"schema:{issue.code} at {issue.path}: {issue.message}" for issue in self.validation.schema_issues),
            *(f"semantic:{issue.code} at {issue.path}: {issue.message}" for issue in self.validation.semantic_issues),
        ]
        return "Shared input bundle failed validation\n" + "\n".join(issues)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-path", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        result = build_daily_context_artifact(
            bundle_path=args.bundle_path,
            user_id=args.user_id,
            date=args.date,
            output_dir=args.output_dir,
        )
    except BundleValidationFailed as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(result["dated_path"])
    print(result["latest_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
