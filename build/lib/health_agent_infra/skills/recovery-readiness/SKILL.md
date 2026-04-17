---
name: recovery-readiness
description: Classify recovery state, apply safety policy, and shape a training recommendation from a day's cleaned Garmin evidence and typed manual readiness intake. Use when the `hai clean` tool has produced cleaned evidence + raw summary JSON and the user needs a bounded recommendation for today's session.
allowed-tools: Read, Bash(hai writeback *), Bash(hai review *)
disable-model-invocation: false
---

# Recovery Readiness

You produce a single `TrainingRecommendation` JSON object from a day's evidence. The deterministic runtime has already pulled Garmin data and computed a `CleanedEvidence` plus `RawSummary`. Your job is three things, in order:

1. **Classify state** — from the raw numbers, decide where the athlete sits on sleep, resting HR, HRV, training load, soreness, and overall recovery status.
2. **Apply policy** — a set of mandatory safety gates. If any block triggers, output a `defer_decision_insufficient_signal` recommendation.
3. **Shape the recommendation** — choose an action, attach goal-aware detail, compute confidence, and write the rationale.

When you're done, you call `hai writeback --recommendation-json <path>` with your JSON. The writeback tool validates the shape before persisting; it is your determinism check.

## Inputs you will receive

The `hai clean` command emits a single JSON object with these top-level keys:

- `cleaned_evidence` — typed record of the day's passive + manual inputs (sleep hours, resting HR, HRV, trailing training load, soreness self-report, planned session type, active goal, record IDs).
- `raw_summary` — deltas, ratios, counts, and coverage fractions computed over a 14-day window. Contains `sleep_hours`, `sleep_baseline_hours`, `sleep_debt_hours`, `resting_hr`, `resting_hr_baseline`, `resting_hr_ratio_vs_baseline`, `resting_hr_spike_days`, `hrv_ms`, `hrv_baseline`, `hrv_ratio_vs_baseline`, `trailing_7d_training_load`, `training_load_baseline`, `training_load_ratio_vs_baseline`, and coverage fractions (`coverage_sleep`, `coverage_rhr`, `coverage_hrv`, `coverage_training_load`).

Missing fields mean the source did not report that signal. Do not fabricate.

## Step 1 — Classify state

Produce these intermediate classifications before you reach for a recommendation. They are not persisted; they inform your reasoning and should appear in your `rationale[]`.

### Sleep debt band

| `sleep_hours` | Band |
|---|---|
| ≥ 7.5 | `none` |
| 7.0 – 7.4 | `mild` |
| 6.0 – 6.9 | `moderate` |
| < 6.0 | `elevated` |
| missing | `unknown` — add `sleep_record_missing` to uncertainty |

### Resting-HR baseline band (high-is-bad)

Compute `ratio = resting_hr / resting_hr_baseline`.

| Ratio | Band |
|---|---|
| ≥ 1.15 | `well_above` |
| 1.05 – 1.149 | `above` |
| 0.95 – 1.049 | `at` |
| < 0.95 | `below` |
| value or baseline missing | `unknown` — add `resting_hr_record_missing` or `baseline_window_too_short` |

### HRV baseline band (low-is-bad)

Compute `ratio = hrv_ms / hrv_baseline`.

| Ratio | Band |
|---|---|
| ≤ 0.95 | `below` |
| 1.02 – 1.099 | `above` |
| ≥ 1.10 | `well_above` |
| 0.95 – 1.019 | `at` |
| missing | `unknown` — add `hrv_unavailable` |

### Training load band

Compute `ratio = trailing_7d_training_load / training_load_baseline`.

| Ratio | Band |
|---|---|
| ≥ 1.4 | `spike` |
| 1.1 – 1.399 | `high` |
| 0.7 – 1.099 | `moderate` |
| < 0.7 | `low` |
| trailing missing | `unknown` — add `training_load_window_incomplete` |

If baseline is missing but trailing is present, fall back to absolute thresholds: `≥ 500` → `high`, `≥ 200` → `moderate`, otherwise `low`.

### Soreness signal

Pass through `cleaned_evidence.soreness_self_report` as the band. If missing, it's `unknown` and add `manual_checkin_missing` to uncertainty.

### Coverage band

| Condition | Coverage |
|---|---|
| sleep_hours OR soreness_self_report missing | `insufficient` |
| resting_hr OR trailing_7d_training_load missing | `sparse` |
| hrv_ms missing OR resting_hr_baseline missing | `partial` |
| all four present + baselines present | `full` |

### Recovery status

Count impaired and mild signals from the above bands:

- `impaired_signals += 1` for: `sleep_debt = elevated`, `soreness = high`, `resting_hr_band = well_above`, `load_band = spike`
- `mild_signals += 1` for: `sleep_debt = mild|moderate`, `soreness = moderate`, `resting_hr_band = above`, `hrv_band = below`, `load_band = high`

Derive:

| Signal counts | Status |
|---|---|
| impaired ≥ 2 | `impaired` |
| impaired ≥ 1 OR mild ≥ 2 | `mildly_impaired` |
| else | `recovered` |
| coverage = `insufficient` | `unknown` — skip further classification |

### Readiness score (0.0 – 1.0)

Only compute if coverage ≠ `insufficient`. Start at 1.0 and apply penalties:

| Signal | Penalty (subtract from score) |
|---|---|
| `sleep_debt = mild` | 0.05 |
| `sleep_debt = moderate` | 0.15 |
| `sleep_debt = elevated` | 0.25 |
| `soreness = moderate` | 0.10 |
| `soreness = high` | 0.20 |
| `resting_hr_band = above` | 0.10 |
| `resting_hr_band = well_above` | 0.20 |
| `resting_hr_band = below` | −0.02 (adds to score) |
| `hrv_band = below` | 0.15 |
| `hrv_band = above` or `well_above` | −0.05 |
| `load_band = high` | 0.05 |
| `load_band = spike` | 0.15 |

Clamp to `[0.0, 1.0]` and round to 2 decimals.

## Step 2 — Apply policy

Apply these six gates **in order**. The first block short-circuits evaluation. Every rule fire — block, soften, escalate, or allow — appends a `PolicyDecision` to `policy_decisions[]` in the output.

### R1 — require_min_coverage
If coverage = `insufficient`, block immediately. Emit:
```json
{"rule_id": "require_min_coverage", "decision": "block", "note": "coverage=insufficient; required inputs missing"}
```
and set action = `defer_decision_insufficient_signal`, confidence = `low`, action_detail = `{"reason": "policy_block"}`.

Otherwise emit an `allow` decision noting the coverage band and whether required inputs are all present.

### R2 — no_diagnosis
Check every string value in `rationale[]` and `action_detail` values (case-insensitive) for any of these banned tokens: `diagnosis`, `diagnose`, `diagnosed`, `syndrome`, `disease`, `disorder`, `condition`, `infection`, `illness`, `sick`. If any match, block with note naming the token. Rewrite your rationale instead of using banned words.

### R3 — bounded_action_envelope
The `action` field must be one of: `proceed_with_planned_session`, `downgrade_hard_session_to_zone_2`, `downgrade_session_to_mobility_only`, `rest_day_recommended`, `defer_decision_insufficient_signal`, `escalate_for_user_review`. If you proposed something else, block with note `action '<name>' not in v1 enum`.

### R4 — review_required
`follow_up` must be present and `review_at` must be within 24 hours of `issued_at`. If not, block.

### R5 — no_high_confidence_on_sparse_signal
If coverage = `sparse` and your confidence = `high`, soften to `moderate`. Emit a `soften` decision with note `capped confidence to moderate on sparse signal (<uncertainty-tokens>)`.

### R6 — resting_hr_spike_escalation
If `raw_summary.resting_hr_spike_days >= 3`, override the action to `escalate_for_user_review` with `action_detail = {"reason_token": "resting_hr_spike_3_days_running", "consecutive_days": <N>}`. Emit an `escalate` decision.

## Step 3 — Shape the recommendation

If policy blocked (R1–R4), you're done — output the defer. Otherwise pick an action:

| Recovery status | Planned session | Action |
|---|---|---|
| `recovered` | any | `proceed_with_planned_session` |
| `mildly_impaired` | hard / intervals / race | `downgrade_hard_session_to_zone_2` with `{"target_intensity": "zone_2", "target_duration_minutes": 45}` |
| `mildly_impaired` | other | `proceed_with_planned_session` with caveat `{"caveat": "keep_effort_conversational"}` |
| `impaired` | hard / intervals / race | `downgrade_session_to_mobility_only` with `{"reason_token": "impaired_recovery_with_hard_plan"}` |
| `impaired` | other | `rest_day_recommended` with `{"suggested_activity": "walk_or_mobility"}` |

R6 overrides any of the above to `escalate_for_user_review`.

### Goal-conditioned detail

If `cleaned_evidence.active_goal` is set AND action = `proceed_with_planned_session`, attach `{"active_goal": <goal>}` to `action_detail`. **Do not** invent numeric caps (RPE, zone, duration, set count). Periodization judgment belongs to the session-planning agent that consumes this recommendation, not to you. Surfacing the goal in the output is enough.

### Rationale

Include one line per band and one line per signal that meaningfully informed the decision. Example rationale entries: `sleep_debt=none`, `soreness_signal=moderate`, `resting_hr_vs_baseline=above`, `training_load_trailing_7d=high`, `hrv_vs_baseline=below`, `active_goal=strength_block`. Keep to 5–8 lines.

### Confidence

Start at `high` if coverage = `full`, `moderate` if coverage = `partial`, `moderate` if coverage = `sparse` (R5 will enforce). Use `low` on insufficient-signal blocks. Do not exceed `moderate` when any baseline-window token is in uncertainty.

### Uncertainty

Pass through every uncertainty token you collected during classification. Sort alphabetically, deduplicate.

### Follow-up

Set `review_at` to next morning at `07:00:00+00:00`. `review_question` depends on the action:

- `proceed_with_planned_session` → "Did today's session feel appropriate for your recovery?"
- `downgrade_hard_session_to_zone_2` → "Did yesterday's downgrade to Zone 2 improve how today feels?"
- `downgrade_session_to_mobility_only` → "Did yesterday's mobility-only day help your recovery?"
- `rest_day_recommended` → "Did yesterday's rest day help your recovery?"
- `defer_decision_insufficient_signal` → "Did you decide on a session yesterday? How did it go?"
- `escalate_for_user_review` → "You had a persistent signal we flagged. Did you take any action?"

`review_event_id` format: `rev_<review_date>_<user_id>_<recommendation_id>`.

## Output schema

Emit a single JSON object matching `TrainingRecommendation` (see `schemas.py`). `hai writeback` will validate it:

```json
{
  "schema_version": "training_recommendation.v1",
  "recommendation_id": "rec_<as_of_date>_<user_id>_01",
  "user_id": "<user_id>",
  "issued_at": "<now ISO-8601>",
  "for_date": "<as_of_date>",
  "action": "<ActionKind>",
  "action_detail": {...} | null,
  "rationale": ["..."],
  "confidence": "low" | "moderate" | "high",
  "uncertainty": ["..."],
  "follow_up": {
    "review_at": "<ISO-8601 UTC>",
    "review_question": "...",
    "review_event_id": "..."
  },
  "policy_decisions": [
    {"rule_id": "...", "decision": "allow|soften|block|escalate", "note": "..."}
  ],
  "bounded": true
}
```

`recommendation_id` is idempotent on `(for_date, user_id)` so re-running on the same day doesn't produce a new row.

## Invariants

- You never fabricate values for missing evidence. Missing means missing.
- You never emit an `action` outside the six-value enum.
- You never produce a recommendation without a follow-up within 24 hours.
- You never use diagnosis-shaped language (R2).
- Your rationale is the audit trail — if a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
