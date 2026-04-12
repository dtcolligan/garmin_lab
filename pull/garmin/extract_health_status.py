from __future__ import annotations

import pandas as pd


def extract_health_status_rows(export_dir) -> list[dict]:
    path = export_dir / "health_status_pivot_export.csv"
    if not path.exists():
        return []
    return pd.read_csv(path).fillna("").to_dict(orient="records")
