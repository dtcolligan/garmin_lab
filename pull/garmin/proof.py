from __future__ import annotations

import json
from pathlib import Path


def write_proof_bundle(proof_dir: Path, payload: dict) -> Path:
    proof_dir.mkdir(parents=True, exist_ok=True)
    path = proof_dir / "proof_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
