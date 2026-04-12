from __future__ import annotations

import json
from pathlib import Path


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "batches": {},
            "daily_fingerprints": {},
            "activity_fingerprints": {},
            "slice_status": {},
            "slice_outputs": {},
            "last_completed_batch_id": None,
        }
    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return path


def mark_slice(state: dict, batch_id: str, slice_id: str, status: str) -> None:
    state.setdefault("slice_status", {}).setdefault(batch_id, {})[slice_id] = status
