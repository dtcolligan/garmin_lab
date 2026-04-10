from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentContractCliIntegrationTest(unittest.TestCase):
    def test_describe_returns_machine_readable_contract_for_submit_and_context_loop(self) -> None:
        result = self._run_cli(["describe"])

        self.assertTrue(result["ok"], msg=result)
        self.assertIsNone(result["error"])
        self.assertTrue(result["validation"]["is_valid"])

        contract = result["contract"]
        self.assertEqual(contract["contract_id"], "health_lab_agent_contract")
        self.assertEqual(contract["contract_version"], "2026-04-10")
        self.assertEqual(contract["discovery"]["command"], "describe")
        self.assertEqual(contract["accepted_enums"]["submit_commands"], ["hydration", "meal"])
        self.assertEqual(contract["accepted_enums"]["context_commands"], ["get", "get-latest"])
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

        context_get = contract["supported_operations"]["context.get"]
        self.assertEqual(context_get["command"], "get")
        self.assertEqual([arg["name"] for arg in context_get["args"]], ["artifact_path", "user_id", "date"])

        produced = contract["artifact_types"]["produced"]
        self.assertEqual(produced[0]["artifact_type"], "agent_readable_daily_context")
        self.assertIn("{output_dir}/agent_readable_daily_context_latest.json", produced[0]["paths"])

    def test_invalid_command_returns_fail_closed_json_error_shape(self) -> None:
        result = self._run_cli(["nope"], expected_returncode=1)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["contract"])
        self.assertFalse(result["validation"]["is_valid"])
        self.assertEqual(result["error"]["code"], "cli_parse_error")
        self.assertIn("invalid choice", result["error"]["message"])
        self.assertEqual(sorted(result.keys()), ["contract", "error", "ok", "validation"])

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_contract_cli", *args],
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
