from __future__ import annotations

import pandas as pd

from .manifest import stable_row_hash


RELEVANT_FAMILIES = {"daily_summary_export.csv", "health_status_pivot_export.csv", "hydration_events_export.csv"}


def extract_daily_fingerprints(export_dir) -> dict[str, str]:
    merged: dict[str, list[tuple[str, str]]] = {}
    for name in RELEVANT_FAMILIES:
        path = export_dir / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "date" not in df.columns:
            continue
        for row in df.fillna("").to_dict(orient="records"):
            date = str(row.get("date") or "")
            if not date:
                continue
            merged.setdefault(date, []).append((name, stable_row_hash(row)))
    return {date: stable_row_hash(dict(parts)) for date, parts in sorted(merged.items())}
