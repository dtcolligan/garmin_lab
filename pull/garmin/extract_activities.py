from __future__ import annotations

import pandas as pd

from .manifest import stable_row_hash


def extract_activity_fingerprints(export_dir) -> dict[str, str]:
    path = export_dir / "activities_export.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "activity_id" not in df.columns:
        return {}
    out: dict[str, str] = {}
    for row in df.fillna("").to_dict(orient="records"):
        activity_id = str(row.get("activity_id") or "")
        if activity_id:
            out[activity_id] = stable_row_hash(row)
    return out
