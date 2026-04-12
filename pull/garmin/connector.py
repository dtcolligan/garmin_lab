from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

from .export_ingest import ingest_export
from .extract_activities import extract_activity_fingerprints
from .extract_daily_summary import extract_daily_fingerprints
from .manifest import build_manifest, write_manifest
from .proof import write_proof_bundle
from .state_store import load_state, mark_slice, save_state
from .types import ConnectorPaths


class GarminExportConnector:
    def __init__(self, paths: ConnectorPaths):
        self.paths = paths

    def run(self, receipt_path: Path, *, stop_after_slices: int | None = None, resume: bool = False) -> dict:
        self.paths.output_dir.mkdir(parents=True, exist_ok=True)
        self.paths.work_dir.mkdir(parents=True, exist_ok=True)
        state = load_state(self.paths.state_path)

        receipt_stage_dir = self.paths.work_dir / receipt_path.stem
        extracted_dir = ingest_export(receipt_path, receipt_stage_dir)
        manifest = build_manifest(receipt_path, extracted_dir)
        manifest_path = write_manifest(manifest, self.paths.output_dir / manifest.batch_id / "manifest.runtime.json")

        current_daily = extract_daily_fingerprints(extracted_dir)
        current_activities = extract_activity_fingerprints(extracted_dir)
        prior_daily = state.get("daily_fingerprints", {})
        prior_activities = state.get("activity_fingerprints", {})

        changed_daily = sorted([date for date, fp in current_daily.items() if prior_daily.get(date) != fp])
        changed_activities = sorted([aid for aid, fp in current_activities.items() if prior_activities.get(aid) != fp])
        slices = [f"day:{date}" for date in changed_daily] + [f"activity:{aid}" for aid in changed_activities]
        processed: list[str] = []

        batch_status = state.setdefault("slice_status", {}).setdefault(manifest.batch_id, {})
        for slice_id in slices:
            if resume and batch_status.get(slice_id) == "completed":
                continue
            mark_slice(state, manifest.batch_id, slice_id, "in_progress")
            save_state(self.paths.state_path, state)
            self._materialize_slice(extracted_dir, manifest.batch_id, slice_id)
            processed.append(slice_id)
            mark_slice(state, manifest.batch_id, slice_id, "completed")
            save_state(self.paths.state_path, state)
            if stop_after_slices is not None and len(processed) >= stop_after_slices:
                state.setdefault("batches", {})[manifest.batch_id] = {
                    "manifest_path": manifest_path.as_posix(),
                    "receipt_path": receipt_path.as_posix(),
                    "status": "interrupted",
                }
                save_state(self.paths.state_path, state)
                return {
                    "batch_id": manifest.batch_id,
                    "manifest_path": manifest_path.as_posix(),
                    "changed_daily": changed_daily,
                    "changed_activities": changed_activities,
                    "processed_slices": processed,
                    "interrupted": True,
                }

        state["daily_fingerprints"] = current_daily
        state["activity_fingerprints"] = current_activities
        state["last_completed_batch_id"] = manifest.batch_id
        state.setdefault("batches", {})[manifest.batch_id] = {
            "manifest_path": manifest_path.as_posix(),
            "receipt_path": receipt_path.as_posix(),
            "status": "completed",
        }
        save_state(self.paths.state_path, state)
        return {
            "batch_id": manifest.batch_id,
            "manifest_path": manifest_path.as_posix(),
            "changed_daily": changed_daily,
            "changed_activities": changed_activities,
            "processed_slices": processed,
            "interrupted": False,
        }

    def _materialize_slice(self, extracted_dir: Path, batch_id: str, slice_id: str) -> None:
        batch_out = self.paths.output_dir / batch_id
        batch_out.mkdir(parents=True, exist_ok=True)
        if slice_id.startswith("day:"):
            key = slice_id.split(":", 1)[1]
            source = extracted_dir / "daily_summary_export.csv"
            target = batch_out / "daily_summary_export.csv"
            self._copy_or_filter_csv(source, target, "date", key)
            optional = extracted_dir / "health_status_pivot_export.csv"
            if optional.exists():
                self._copy_or_filter_csv(optional, batch_out / "health_status_pivot_export.csv", "date", key, append=True)
            hyd = extracted_dir / "hydration_events_export.csv"
            if hyd.exists():
                self._copy_or_filter_csv(hyd, batch_out / "hydration_events_export.csv", "date", key, append=True)
        elif slice_id.startswith("activity:"):
            key = slice_id.split(":", 1)[1]
            source = extracted_dir / "activities_export.csv"
            target = batch_out / "activities_export.csv"
            self._copy_or_filter_csv(source, target, "activity_id", key)

    def _copy_or_filter_csv(self, source: Path, target: Path, column: str, match: str, *, append: bool = False) -> None:
        import pandas as pd

        df = pd.read_csv(source)
        if column not in df.columns:
            return
        filtered = df[df[column].astype(str) == str(match)]
        if filtered.empty:
            return
        if append and target.exists():
            existing = pd.read_csv(target)
            filtered = pd.concat([existing, filtered], ignore_index=True).drop_duplicates().reset_index(drop=True)
        filtered.to_csv(target, index=False)


def run_connector(receipt_path: Path, state_path: Path, output_dir: Path, work_dir: Path, *, stop_after_slices: int | None = None, resume: bool = False, proof_dir: Path | None = None) -> dict:
    connector = GarminExportConnector(ConnectorPaths(state_path=state_path, output_dir=output_dir, work_dir=work_dir))
    result = connector.run(receipt_path, stop_after_slices=stop_after_slices, resume=resume)
    if proof_dir is not None:
        state = load_state(state_path)
        proof_payload = {
            "batch_id": result["batch_id"],
            "manifest_path": result["manifest_path"],
            "changed_daily": result["changed_daily"],
            "changed_activities": result["changed_activities"],
            "processed_slices": result["processed_slices"],
            "interrupted": result["interrupted"],
            "slice_status": state.get("slice_status", {}).get(result["batch_id"], {}),
        }
        proof_manifest = write_proof_bundle(proof_dir, proof_payload)
        result["proof_manifest"] = proof_manifest.as_posix()
    return result
