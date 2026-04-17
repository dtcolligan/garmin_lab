---
name: merge-human-inputs
description: Take a raw human input — typed note, voice transcript, structured answer — and partition it into the master dataset slots the deterministic runtime expects. Use when the user volunteers information outside a structured form, or when typed manual readiness is needed for the flagship loop.
allowed-tools: Read, Write, Bash(hai pull *), Bash(hai intake *)
disable-model-invocation: false
---

# Merge Human Inputs

You receive unstructured human input and route the content into typed slots the runtime can store. You are **not** interpreting the content's meaning — you're partitioning it by topic. Interpretation (classification, recommendation) is a separate skill's job.

## Master dataset slots (v1)

- **Subjective recovery** — soreness, fatigue, perceived sleep quality, energy, stress. Keys: `soreness`, `energy`, `planned_session_type`, `active_goal`, free-text `notes`.
- **Session log** — retrospective report of a completed training session. Keys: `date`, `type`, `duration_minutes`, `perceived_effort`, free-text notes.
- **Nutrition** — meals, hydration, supplements. Keys: `meal_type`, `items`, `time`.
- **Context notes** — anything the user wants on file that isn't one of the above. Stored as-is with `date` and free text.

## Typed manual readiness intake (flagship hot path)

When the user is starting a day and hasn't yet done their readiness check, ask for the four fields the flagship loop needs:

1. **Soreness** — `low` / `moderate` / `high`. ("On a 0-10 scale, 0-3 is low, 4-6 moderate, 7+ high.")
2. **Energy** — `low` / `moderate` / `high`. Same mapping.
3. **Planned session** — free text, but encourage one of: `easy`, `moderate`, `hard`, `intervals`, `race`, `rest`. If the user says "I'm going for a 10k tempo run", route to `hard`. If the user says "probably mobility", route to `moderate` or `rest` depending on intent.
4. **Active goal** — free text. Examples: `strength_block`, `endurance_taper`, `5k_pr_build`, `marathon_base`, `bf_reduction`, `movement_maintenance`. Whatever the user says — this is their framing, not yours.

Use `hai intake readiness` to emit a validated JSON blob to stdout:

```bash
hai intake readiness --soreness moderate --energy high \
                     --planned-session-type hard --active-goal strength_block \
                     > /tmp/mr.json
hai pull --date 2026-04-17 --manual-readiness-json /tmp/mr.json > /tmp/evidence.json
```

`--soreness` and `--energy` are enum-constrained by the CLI (`low | moderate | high`); `--planned-session-type` and `--active-goal` are free text. The command emits a JSON object with those fields plus a `submission_id` of shape `m_ready_<as_of>_<timestamp>`.

If you're hand-crafting JSON for a fixture or replaying a capture, you can skip `hai intake readiness` and write the object directly to a file, then pass it to `hai pull --manual-readiness-json`. The pull step attaches the payload to the evidence it emits, so `hai clean` sees the soreness / energy / goal under `cleaned_evidence`.

## When the user volunteers unstructured input

Example: "I slept badly, woke up sore, trying to push volume this week."

Partition:

- "slept badly" → `subjective_recovery.notes` (don't try to quantify)
- "woke up sore" → `subjective_recovery.soreness = moderate` (ask for confirmation if they haven't used the scale)
- "trying to push volume this week" → `subjective_recovery.active_goal = volume_push_week` (or similar; use the user's framing)

Then confirm with the user before writing: "I'd log this as sore=moderate, goal=volume_push_week, plus a free-text note about sleep. Good?"

## If you're uncertain where a field goes

Ask one targeted clarifying question, not a wall of options. "Is this about today's recovery or a past session?" resolves most ambiguity.

## Never

- Silently reclassify the user's framing. If they say "active_goal: feel good", that's the goal. Don't rename it to `general_wellbeing`.
- Add signals the user didn't report. If they mentioned sleep but not HRV, don't infer an HRV value.
- Route medical or diagnostic language to any slot. If the user says "I think I have COVID", refuse to log that as recovery data and point them to a clinician. Follow the safety skill's rules.
