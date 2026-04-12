from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .types import BatchManifest, FileManifestEntry, PARSER_VERSION


EXPORT_FILES = [
    "daily_summary_export.csv",
    "activities_export.csv",
    "health_status_pivot_export.csv",
    "hydration_events_export.csv",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_dir():
        for child in sorted(p for p in path.rglob("*") if p.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            with child.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    digest.update(chunk)
        return digest.hexdigest()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_row_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def file_coverage(name: str, df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    if name == "daily_summary_export.csv":
        return [str(v) for v in df.get("date", pd.Series(dtype=str)).dropna().astype(str).tolist()]
    if name == "health_status_pivot_export.csv":
        return [str(v) for v in df.get("date", pd.Series(dtype=str)).dropna().astype(str).tolist()]
    if name == "hydration_events_export.csv":
        return sorted({str(v) for v in df.get("date", pd.Series(dtype=str)).dropna().astype(str).tolist()})
    if name == "activities_export.csv":
        return [str(v) for v in df.get("activity_id", pd.Series(dtype=str)).dropna().astype(str).tolist()]
    return []


def build_manifest(receipt_path: Path, extracted_dir: Path) -> BatchManifest:
    file_entries: list[FileManifestEntry] = []
    batch_hash_parts = [sha256_path(receipt_path)]
    for name in EXPORT_FILES:
        path = extracted_dir / name
        df = load_frame(path)
        file_hash = sha256_path(path) if path.exists() else hashlib.sha256(b"").hexdigest()
        batch_hash_parts.append(f"{name}:{file_hash}")
        file_entries.append(
            FileManifestEntry(
                name=name,
                path=path.as_posix(),
                sha256=file_hash,
                rows=int(len(df.index)) if not df.empty else 0,
                coverage=file_coverage(name, df),
            )
        )
    batch_id = hashlib.sha256("|".join(batch_hash_parts).encode("utf-8")).hexdigest()[:16]
    return BatchManifest(
        batch_id=batch_id,
        receipt_type="directory" if receipt_path.is_dir() else "zip",
        receipt_path=receipt_path.as_posix(),
        receipt_sha256=sha256_path(receipt_path),
        parser_version=PARSER_VERSION,
        files=file_entries,
    )


def write_manifest(manifest: BatchManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return path
