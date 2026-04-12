from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pull.garmin.connector import run_connector


class GarminExportRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = Path("pull/garmin/fixtures")

    def test_replay_is_stable_for_same_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"
            proof = root / "proof"

            first = run_connector(self.fixtures / "baseline_export", state, output, work, proof_dir=proof)
            second = run_connector(self.fixtures / "baseline_export", state, output, work, proof_dir=proof)

            self.assertEqual(first["batch_id"], second["batch_id"])
            self.assertEqual(second["changed_daily"], [])
            self.assertEqual(second["changed_activities"], [])
            self.assertEqual(second["processed_slices"], [])

    def test_followup_only_reprocesses_changed_day_and_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"

            run_connector(self.fixtures / "baseline_export", state, output, work)
            follow = run_connector(self.fixtures / "followup_export", state, output, work)

            self.assertEqual(follow["changed_daily"], ["2026-04-02"])
            self.assertEqual(follow["changed_activities"], ["1002"])
            self.assertEqual(follow["processed_slices"], ["day:2026-04-02", "activity:1002"])

    def test_resume_continues_from_first_incomplete_slice_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"

            run_connector(self.fixtures / "baseline_export", state, output, work)
            interrupted = run_connector(
                self.fixtures / "followup_export",
                state,
                output,
                work,
                stop_after_slices=1,
            )
            self.assertTrue(interrupted["interrupted"])
            resumed = run_connector(
                self.fixtures / "followup_export",
                state,
                output,
                work,
                resume=True,
            )
            self.assertFalse(resumed["interrupted"])
            self.assertEqual(resumed["processed_slices"], ["activity:1002"])

            status = json.loads(state.read_text())["slice_status"][resumed["batch_id"]]
            self.assertEqual(status["day:2026-04-02"], "completed")
            self.assertEqual(status["activity:1002"], "completed")


if __name__ == "__main__":
    unittest.main()
