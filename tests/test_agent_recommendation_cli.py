from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "agent_readable_daily_context" / "generated_fixture_day_context.json"


class AgentRecommendationCliIntegrationTest(unittest.TestCase):
    def test_create_writes_dated_and_latest_recommendation_for_valid_scoped_context(self) -> None:
        context = json.loads(CONTEXT_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            payload = {
                "user_id": "user_1",
                "date": "2026-04-09",
                "context_artifact_path": str(CONTEXT_FIXTURE),
                "context_artifact_id": context["context_id"],
                "recommendation_id": "rec_20260409_recovery_01",
                "summary": "Keep training easy and prioritize recovery inputs today.",
                "rationale": "Low energy, reported soreness, and completed training already point to a lower-load day.",
                "evidence_refs": ["subjective_voice_20260409", "manual_gym_session_20260409"],
                "confidence_score": 0.82,
            }

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)])

            self.assertTrue(result["ok"], msg=result)
            self.assertIsNone(result["error"])
            self.assertTrue(result["validation"]["is_valid"])
            self.assertEqual(result["recommendation"]["artifact_type"], "agent_recommendation")
            self.assertEqual(result["recommendation"]["context_artifact_path"], str(CONTEXT_FIXTURE))
            self.assertEqual(result["recommendation"]["context_artifact_id"], context["context_id"])
            self.assertEqual(result["recommendation"]["evidence_refs"], payload["evidence_refs"])

            dated_path = Path(result["artifact_path"])
            latest_path = Path(result["latest_artifact_path"])
            self.assertTrue(dated_path.exists())
            self.assertTrue(latest_path.exists())
            self.assertEqual(dated_path.read_bytes(), latest_path.read_bytes())
            self.assertEqual(json.loads(dated_path.read_text()), result["recommendation"])

    def test_create_rejects_bad_user_scope_with_fail_closed_envelope(self) -> None:
        context = json.loads(CONTEXT_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            payload = {
                "user_id": "wrong_user",
                "date": "2026-04-09",
                "context_artifact_path": str(CONTEXT_FIXTURE),
                "context_artifact_id": context["context_id"],
                "recommendation_id": "rec_bad_scope_01",
                "summary": "Summary",
                "rationale": "Rationale",
                "evidence_refs": ["subjective_voice_20260409"],
                "confidence_score": 0.8,
            }

            result = self._run_cli(
                ["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertIsNone(result["artifact_path"])
            self.assertIsNone(result["latest_artifact_path"])
            self.assertIsNone(result["recommendation"])
            self.assertEqual(result["error"]["code"], "artifact_user_mismatch")
            self.assertTrue(any(issue["code"] == "artifact_user_mismatch" for issue in result["validation"]["semantic_issues"]))

    def test_create_rejects_ungrounded_evidence_ref_with_fail_closed_envelope(self) -> None:
        context = json.loads(CONTEXT_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            payload = {
                "user_id": "user_1",
                "date": "2026-04-09",
                "context_artifact_path": str(CONTEXT_FIXTURE),
                "context_artifact_id": context["context_id"],
                "recommendation_id": "rec_bad_evidence_01",
                "summary": "Summary",
                "rationale": "Rationale",
                "evidence_refs": ["not_in_context"],
                "confidence_score": 0.8,
            }

            result = self._run_cli(
                ["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "ungrounded_evidence_ref")
            self.assertTrue(any(issue["code"] == "ungrounded_evidence_ref" for issue in result["validation"]["semantic_issues"]))

    def test_create_rejects_missing_context_artifact_with_fail_closed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            missing_context_path = Path(temp_dir) / "missing_context.json"
            payload = {
                "user_id": "user_1",
                "date": "2026-04-09",
                "context_artifact_path": str(missing_context_path),
                "context_artifact_id": "agent_context_user_1_2026-04-09",
                "recommendation_id": "rec_missing_context_01",
                "summary": "Summary",
                "rationale": "Rationale",
                "evidence_refs": ["subjective_voice_20260409"],
                "confidence_score": 0.8,
            }

            result = self._run_cli(
                ["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "context_artifact_not_found")
            self.assertTrue(any(issue["code"] == "context_artifact_not_found" for issue in result["validation"]["semantic_issues"]))

    def test_rejected_create_leaves_preexisting_recommendation_artifacts_byte_identical(self) -> None:
        context = json.loads(CONTEXT_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            health_dir.mkdir(parents=True, exist_ok=True)
            dated_path = health_dir / "agent_recommendation_2026-04-09.json"
            latest_path = health_dir / "agent_recommendation_latest.json"
            original_bytes = (
                json.dumps(
                    {
                        "artifact_type": "agent_recommendation",
                        "user_id": "user_1",
                        "date": "2026-04-09",
                        "context_artifact_path": str(CONTEXT_FIXTURE),
                        "context_artifact_id": context["context_id"],
                        "recommendation_id": "rec_existing_01",
                        "summary": "Existing recommendation.",
                        "rationale": "Existing rationale.",
                        "evidence_refs": ["subjective_voice_20260409"],
                        "confidence_score": 0.7,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode()
            dated_path.write_bytes(original_bytes)
            latest_path.write_bytes(original_bytes)

            payload = {
                "user_id": "user_1",
                "date": "2026-04-09",
                "context_artifact_path": str(CONTEXT_FIXTURE),
                "context_artifact_id": context["context_id"],
                "recommendation_id": "rec_rejected_01",
                "summary": "Summary",
                "rationale": "Rationale",
                "evidence_refs": ["not_in_context"],
                "confidence_score": 0.8,
            }

            result = self._run_cli(
                ["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "ungrounded_evidence_ref")
            self.assertTrue(result["error"])
            self.assertEqual(dated_path.read_bytes(), original_bytes)
            self.assertEqual(latest_path.read_bytes(), original_bytes)

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_recommendation_cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected_returncode, msg=completed.stderr or completed.stdout)
        self.assertEqual(completed.stderr.strip(), "")
        self.assertTrue(completed.stdout.strip())
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
