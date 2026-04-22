"""Tests for `hai classify` + `hai policy` debug CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _write_clean_bundle(tmp_path: Path, **overrides) -> Path:
    """Write a minimal `hai clean` output JSON that classify/policy accept."""

    bundle = {
        "cleaned_evidence": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "sleep_hours": 8.0,
            "resting_hr": 52.0,
            "hrv_ms": 80.0,
            "soreness_self_report": "low",
        },
        "raw_summary": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "resting_hr_baseline": 52.0,
            "resting_hr_ratio_vs_baseline": 1.0,
            "hrv_ratio_vs_baseline": 1.0,
            "trailing_7d_training_load": 400.0,
            "training_load_baseline": 400.0,
            "training_load_ratio_vs_baseline": 1.0,
            "resting_hr_spike_days": 0,
        },
    }
    for key, value in overrides.items():
        if key in bundle["cleaned_evidence"]:
            bundle["cleaned_evidence"][key] = value
        else:
            bundle["raw_summary"][key] = value
    path = tmp_path / "cleaned.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# hai classify
# ---------------------------------------------------------------------------

def test_cli_classify_emits_classified_state(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path)
    rc = cli_main(
        ["classify", "--domain", "recovery", "--evidence-json", str(bundle_path)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["domain"] == "recovery"
    assert payload["classified"]["coverage_band"] == "full"
    assert payload["classified"]["recovery_status"] == "recovered"
    assert payload["classified"]["readiness_score"] == 1.0


def test_cli_classify_rejects_unknown_domain(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path)
    # argparse --choices rejects before we get to the function body, so it
    # exits non-zero with an argparse error, not our cleaner exit=2.
    with pytest.raises(SystemExit):
        cli_main(
            ["classify", "--domain", "nutrition", "--evidence-json", str(bundle_path)]
        )


def test_cli_classify_missing_evidence_file_fails_clean(tmp_path: Path, capsys):
    missing = tmp_path / "nonexistent.json"
    rc = cli_main(
        ["classify", "--domain", "recovery", "--evidence-json", str(missing)]
    )
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "not found" in err


def test_cli_classify_malformed_evidence_json(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    rc = cli_main(
        ["classify", "--domain", "recovery", "--evidence-json", str(bad)]
    )
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "not valid JSON" in err


def test_cli_classify_bundle_missing_required_keys(tmp_path: Path, capsys):
    bad = tmp_path / "missing_keys.json"
    bad.write_text(json.dumps({"evidence": {}}), encoding="utf-8")
    rc = cli_main(
        ["classify", "--domain", "recovery", "--evidence-json", str(bad)]
    )
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "cleaned_evidence" in err or "raw_summary" in err


def test_cli_classify_uses_thresholds_override(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path, sleep_hours=7.7)
    toml_path = tmp_path / "thresholds.toml"
    toml_path.write_text(
        "[classify.recovery.sleep_debt_band]\n"
        "none_min_hours = 8.0\n",
        encoding="utf-8",
    )
    rc = cli_main([
        "classify", "--domain", "recovery",
        "--evidence-json", str(bundle_path),
        "--thresholds-path", str(toml_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # 7.7h is "none" at default 7.5; "mild" under the overridden 8.0.
    assert payload["classified"]["sleep_debt_band"] == "mild"


# ---------------------------------------------------------------------------
# hai policy
# ---------------------------------------------------------------------------

def test_cli_policy_emits_classified_and_policy(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path)
    rc = cli_main(
        ["policy", "--domain", "recovery", "--evidence-json", str(bundle_path)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "classified" in payload
    assert "policy" in payload
    assert len(payload["policy"]["policy_decisions"]) == 3
    assert payload["policy"]["forced_action"] is None


def test_cli_policy_surfaces_r6_escalation(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path, resting_hr_spike_days=5)
    rc = cli_main(
        ["policy", "--domain", "recovery", "--evidence-json", str(bundle_path)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy"]["forced_action"] == "escalate_for_user_review"
    assert payload["policy"]["forced_action_detail"]["consecutive_days"] == 5


def test_cli_policy_surfaces_r1_defer_on_insufficient(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path, sleep_hours=None)
    rc = cli_main(
        ["policy", "--domain", "recovery", "--evidence-json", str(bundle_path)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy"]["forced_action"] == "defer_decision_insufficient_signal"


def test_cli_policy_fails_on_malformed_thresholds(tmp_path: Path, capsys):
    bundle_path = _write_clean_bundle(tmp_path)
    bad = tmp_path / "bad.toml"
    bad.write_text("lol = = =", encoding="utf-8")
    rc = cli_main([
        "policy", "--domain", "recovery",
        "--evidence-json", str(bundle_path),
        "--thresholds-path", str(bad),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "config error" in err
