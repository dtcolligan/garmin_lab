from __future__ import annotations

from pathlib import Path

from .manifest import EXPORT_FILES


REQUIRED_EXPORTS = ("daily_summary_export.csv", "activities_export.csv")


def discover_export_files(export_dir: Path) -> dict[str, Path]:
    return {name: export_dir / name for name in EXPORT_FILES if (export_dir / name).exists()}


def validate_export_dir(export_dir: Path) -> None:
    missing = [name for name in REQUIRED_EXPORTS if not (export_dir / name).exists()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Garmin export fixture is missing required files: {joined}")
