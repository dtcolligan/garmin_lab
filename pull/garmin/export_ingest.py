from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from .discovery import validate_export_dir


EXPORT_GLOB = "*_export.csv"


def ingest_export(receipt_path: Path, batch_dir: Path) -> Path:
    batch_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir = batch_dir / "extracted"
    if extracted_dir.exists():
        shutil.rmtree(extracted_dir)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    if receipt_path.is_dir():
        for child in receipt_path.iterdir():
            if child.is_file() and (child.name.endswith(".csv") or child.name == "manifest.json"):
                shutil.copy2(child, extracted_dir / child.name)
    else:
        with zipfile.ZipFile(receipt_path) as zf:
            for member in zf.namelist():
                name = Path(member).name
                if name.endswith(".csv") or name == "manifest.json":
                    target = extracted_dir / name
                    target.write_bytes(zf.read(member))
    validate_export_dir(extracted_dir)
    return extracted_dir
