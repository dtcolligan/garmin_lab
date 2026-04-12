from __future__ import annotations

import pandas as pd


def extract_hydration_rows(export_dir) -> list[dict]:
    path = export_dir / "hydration_events_export.csv"
    if not path.exists():
        return []
    return pd.read_csv(path).fillna("").to_dict(orient="records")
