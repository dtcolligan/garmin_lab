from __future__ import annotations

import argparse
from pathlib import Path

from .connector import run_connector


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = PROJECT_ROOT / "pull" / "data" / "garmin" / "runtime_state.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reporting" / "artifacts" / "protocol_layer_proof" / "garmin_export_runtime"
DEFAULT_WORK = PROJECT_ROOT / "pull" / "data" / "garmin" / "runtime_work"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Garmin export runtime hardening slice")
    parser.add_argument("receipt_path")
    parser.add_argument("--state-path", default=str(DEFAULT_STATE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--proof-dir")
    parser.add_argument("--stop-after-slices", type=int)
    parser.add_argument("--resume", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_connector(
        Path(args.receipt_path),
        Path(args.state_path),
        Path(args.output_dir),
        Path(args.work_dir),
        stop_after_slices=args.stop_after_slices,
        resume=args.resume,
        proof_dir=Path(args.proof_dir) if args.proof_dir else None,
    )
    print(result)


if __name__ == "__main__":
    main()
