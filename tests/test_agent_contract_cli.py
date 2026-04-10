from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VOICE_NOTE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "voice_note_intake" / "daily_voice_note_input.json"


class AgentContractCliIntegrationTest(unittest.TestCase):
    def test_describe_returns_machine_readable_contract_for_bootstrap_submit_context_and_recommendation_loop(self) -> None:
        result = self._run_cli(["describe"])

        self.assertTrue(result["ok"], msg=result)
        self.assertIsNone(result["error"])
        self.assertTrue(result["validation"]["is_valid"])

        contract = result["contract"]
        self.assertEqual(contract["contract_id"], "health_lab_agent_contract")
        self.assertEqual(contract["contract_version"], "2026-04-10")
        self.assertEqual(contract["discovery"]["command"], "describe")
        self.assertEqual(contract["accepted_enums"]["bundle_commands"], ["init"])
        self.assertEqual(contract["accepted_enums"]["submit_commands"], ["hydration", "meal"])
        self.assertEqual(contract["accepted_enums"]["voice_note_commands"], ["submit"])
        self.assertEqual(contract["accepted_enums"]["voice_note_payload_inputs"], ["payload_json", "payload_path"])
        self.assertEqual(contract["accepted_enums"]["context_commands"], ["get", "get-latest"])
        self.assertEqual(contract["accepted_enums"]["recommendation_commands"], ["create"])
        self.assertEqual(contract["accepted_enums"]["recommendation_payload_inputs"], ["payload_json", "payload_path"])
        self.assertEqual(contract["accepted_enums"]["completeness_state"], ["partial", "complete", "corrected"])
        self.assertEqual(contract["accepted_enums"]["estimated"], ["true", "false"])
        self.assertEqual(
            contract["path_conventions"]["dated_context_artifact"],
            "{output_dir}/agent_readable_daily_context_{date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_context_artifact"],
            "{output_dir}/agent_readable_daily_context_latest.json",
        )
        self.assertEqual(
            contract["path_conventions"]["dated_recommendation_artifact"],
            "{output_dir}/agent_recommendation_{date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_recommendation_artifact"],
            "{output_dir}/agent_recommendation_latest.json",
        )

        bootstrap_init = contract["supported_operations"]["bootstrap.init"]
        self.assertEqual(bootstrap_init["module"], "health_model.agent_bundle_cli")
        self.assertEqual(bootstrap_init["command"], "init")
        self.assertEqual(bootstrap_init["mode"], "write")
        self.assertEqual([arg["name"] for arg in bootstrap_init["args"]], ["bundle_path", "user_id", "date"])

        submit_hydration = contract["supported_operations"]["submit.hydration"]
        hydration_flags = {arg["flag"] for arg in submit_hydration["args"]}
        self.assertIn("--bundle-path", hydration_flags)
        self.assertIn("--amount-ml", hydration_flags)
        self.assertIn("--beverage-type", hydration_flags)
        self.assertIn("--completeness-state", hydration_flags)

        submit_meal = contract["supported_operations"]["submit.meal"]
        meal_args = {arg["name"]: arg for arg in submit_meal["args"]}
        self.assertEqual(meal_args["estimated"]["accepted_values"], ["true", "false"])
        self.assertTrue(meal_args["note_text"]["required"])
        self.assertFalse(meal_args["meal_label"]["required"])

        submit_voice_note = contract["supported_operations"]["submit.voice_note"]
        voice_note_args = {arg["name"]: arg for arg in submit_voice_note["args"]}
        self.assertEqual(submit_voice_note["module"], "health_model.agent_voice_note_cli")
        self.assertEqual(submit_voice_note["command"], "submit")
        self.assertEqual(submit_voice_note["consumes"], ["shared_input_bundle", "voice_note_submission_payload"])
        self.assertEqual(
            submit_voice_note["produces"],
            ["shared_input_bundle", "agent_readable_daily_context_dated", "agent_readable_daily_context_latest"],
        )
        self.assertEqual(voice_note_args["payload_json"]["type"], "json_object")
        self.assertFalse(voice_note_args["payload_json"]["required"])
        self.assertFalse(voice_note_args["payload_path"]["required"])

        context_get = contract["supported_operations"]["context.get"]
        self.assertEqual(context_get["command"], "get")
        self.assertEqual([arg["name"] for arg in context_get["args"]], ["artifact_path", "user_id", "date"])

        recommendation_create = contract["supported_operations"]["recommendation.create"]
        recommendation_args = {arg["name"]: arg for arg in recommendation_create["args"]}
        self.assertEqual(recommendation_create["module"], "health_model.agent_recommendation_cli")
        self.assertEqual(recommendation_create["command"], "create")
        self.assertEqual(recommendation_create["consumes"], ["agent_readable_daily_context"])
        self.assertEqual(recommendation_create["produces"], ["agent_recommendation_dated", "agent_recommendation_latest"])
        self.assertEqual(
            recommendation_create["payload_shape"]["required_fields"],
            [
                "user_id",
                "date",
                "context_artifact_path",
                "context_artifact_id",
                "recommendation_id",
                "summary",
                "rationale",
                "evidence_refs",
                "confidence_score",
            ],
        )
        self.assertEqual(recommendation_args["payload_json"]["type"], "json_object")
        self.assertFalse(recommendation_args["payload_json"]["required"])
        self.assertFalse(recommendation_args["payload_path"]["required"])

        consumed = contract["artifact_types"]["consumed"]
        self.assertEqual(consumed[2]["artifact_type"], "voice_note_submission_payload")
        self.assertIn("--payload-path", consumed[2]["shape"])

        produced = contract["artifact_types"]["produced"]
        self.assertEqual(produced[0]["artifact_type"], "shared_input_bundle")
        self.assertIn("{output_dir}/shared_input_bundle_{date}.json", produced[0]["paths"])
        self.assertEqual(produced[1]["artifact_type"], "agent_readable_daily_context")
        self.assertIn("{output_dir}/agent_readable_daily_context_latest.json", produced[1]["paths"])
        self.assertIn("submit.voice_note", produced[1]["notes"])
        self.assertEqual(produced[2]["artifact_type"], "agent_recommendation")
        self.assertIn("{output_dir}/agent_recommendation_latest.json", produced[2]["paths"])
        self.assertIn("recommendation.create", produced[2]["notes"])
        self.assertEqual(
            contract["response_envelopes"]["bootstrap.init"]["success_keys"],
            ["ok", "bundle_path", "bundle", "validation", "error"],
        )
        self.assertEqual(
            contract["response_envelopes"]["recommendation.create"]["success_keys"],
            ["ok", "artifact_path", "latest_artifact_path", "recommendation", "validation", "error"],
        )

    def test_contract_describe_bootstrap_voice_note_submit_and_context_get_prove_external_agent_loop(self) -> None:
        contract_result = self._run_cli(["describe"])
        submit_voice_note = contract_result["contract"]["supported_operations"]["submit.voice_note"]

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            dated_artifact_path = health_dir / "agent_readable_daily_context_2026-04-09.json"

            bootstrap = self._run_module(
                "health_model.agent_bundle_cli",
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )
            submit = self._run_module(
                submit_voice_note["module"],
                [
                    submit_voice_note["command"],
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-path",
                    str(VOICE_NOTE_FIXTURE),
                ],
            )
            context = self._run_module(
                "health_model.agent_context_cli",
                [
                    "get",
                    "--artifact-path",
                    str(dated_artifact_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )

            self.assertTrue(bootstrap["ok"], msg=bootstrap)
            self.assertTrue(submit["ok"], msg=submit)
            self.assertTrue(context["ok"], msg=context)
            self.assertEqual(submit["bundle_path"], str(bundle_path))
            self.assertEqual(submit["dated_artifact_path"], str(dated_artifact_path))
            self.assertEqual(
                submit["accepted_provenance"],
                {
                    "source_artifact_ids": ["artifact_01JQVOICEINTAKE01"],
                    "input_event_ids": ["event_01JQVOICECAF1", "event_01JQVOICELEGS1"],
                    "subjective_entry_ids": ["subjective_01JQVOICESUBJ01"],
                    "manual_log_entry_ids": [],
                },
            )

            generated_from = context["context"]["generated_from"]
            self.assertIn("artifact_01JQVOICEINTAKE01", generated_from["source_artifact_ids"])
            self.assertIn("event_01JQVOICECAF1", generated_from["input_event_ids"])
            self.assertIn("event_01JQVOICELEGS1", generated_from["input_event_ids"])
            self.assertEqual(generated_from["subjective_entry_ids"], ["subjective_01JQVOICESUBJ01"])

            subjective_signal = next(
                signal
                for signal in context["context"]["explicit_grounding"]["signals"]
                if signal["domain"] == "subjective_state" and signal["signal_key"] == "energy"
            )
            self.assertEqual(subjective_signal["value"], 2)
            self.assertTrue(subjective_signal["evidence_refs"])

    def test_invalid_command_returns_fail_closed_json_error_shape(self) -> None:
        result = self._run_cli(["nope"], expected_returncode=1)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["contract"])
        self.assertFalse(result["validation"]["is_valid"])
        self.assertEqual(result["error"]["code"], "cli_parse_error")
        self.assertIn("invalid choice", result["error"]["message"])
        self.assertEqual(sorted(result.keys()), ["contract", "error", "ok", "validation"])

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        return self._run_module("health_model.agent_contract_cli", args, expected_returncode=expected_returncode)

    def _run_module(self, module: str, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", module, *args],
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
