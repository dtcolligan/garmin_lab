---
name: writeback-protocol
description: Persist a TrainingRecommendation or ReviewOutcome to the local state via the `hai writeback` and `hai review` tools. Use when a recommendation is ready to ship or when an outcome needs recording.
allowed-tools: Bash(hai writeback *), Bash(hai review *), Read, Write
disable-model-invocation: false
---

# Writeback Protocol

You don't persist anything yourself. The `hai` CLI owns all local state mutation. Your job is to call the right subcommand with validated input.

## Recommendation writeback

Once the recovery-readiness skill has produced a `TrainingRecommendation` JSON, write it to a temp file and invoke:

```bash
hai writeback --recommendation-json /path/to/recommendation.json \
              --base-dir <writeback_root>
```

The `<writeback_root>` must end in `recovery_readiness_v1/` — the writeback tool enforces this via the `writeback_locality` check and rejects anything else. Typical local root: `~/.local/share/health_agent_infra/recovery_readiness_v1/` or `/tmp/recovery_readiness_v1/` for scratch runs.

The tool will:

1. Parse and validate the JSON against the `TrainingRecommendation` schema. Malformed JSON or wrong-shape fields fail closed — the tool exits non-zero with a clear error message, nothing persists.
2. Append to `recommendation_log.jsonl` if `recommendation_id` isn't already present. Idempotent — re-running is safe.
3. Append a markdown entry to `daily_plan_<for_date>.md` with a marker so repeated runs don't duplicate.
4. Return an `ActionRecord` confirming the paths written to.

If validation fails, fix the JSON and retry. **Do not** attempt to write files directly — the idempotency and locality guarantees live inside the tool.

## Review scheduling

After the recommendation writeback succeeds, schedule the follow-up review:

```bash
hai review schedule --recommendation-json /path/to/recommendation.json \
                    --base-dir <writeback_root>
```

This appends to `review_events.jsonl` using the `follow_up.review_event_id` from the recommendation. Idempotent on `review_event_id`.

## Review outcome recording

When the user reports whether yesterday's recommendation helped, construct a `ReviewOutcome` JSON:

```json
{
  "review_event_id": "rev_2026-04-18_user_rec_2026-04-17_user_01",
  "recommendation_id": "rec_2026-04-17_user_01",
  "user_id": "user",
  "recorded_at": "2026-04-18T08:00:00+00:00",
  "followed_recommendation": true,
  "self_reported_improvement": true,
  "free_text": "felt good, hit all intervals"
}
```

Then:

```bash
hai review record --outcome-json /path/to/outcome.json \
                  --base-dir <writeback_root>
```

Appends to `review_outcomes.jsonl`. **Not idempotent** — outcomes are append-only, so don't call twice for the same event unless deliberately.

## Summarising review history

For the reporting skill or for your own context:

```bash
hai review summary --base-dir <writeback_root> [--user-id <id>]
```

Emits counts by outcome category (`total`, `followed_improved`, `followed_no_change`, `followed_unknown`, `not_followed`). This is bookkeeping — no classifier inference.

## Invariants

- All state mutation goes through `hai`. Never edit JSONL files directly.
- The writeback tool is the schema validator. If it rejects your JSON, the JSON was wrong; fix it, don't bypass.
- `recommendation_id` is the idempotency key for recommendations; `review_event_id` for events. Outcomes append unconditionally.
- Writeback path must be inside a directory named `recovery_readiness_v1` — this is enforced at the I/O boundary.
