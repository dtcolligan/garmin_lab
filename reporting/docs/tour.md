# Reading Tour

A 10-minute guided read of Health Agent Infra, for someone (including future-you) who is coming back cold.

## 1. What you're looking at

Health Agent Infra is **agent infrastructure**, not a health app. It ships two things to an agent like Claude Code:

- **A CLI called `hai`** with deterministic subcommands: `hai intake`, `hai pull`, `hai clean`, `hai writeback`, `hai review`, `hai setup-skills`.
- **A `skills/` directory** with five markdown skills the agent reads to decide what to do with the evidence the CLI emits.

The agent owns all judgment — state classification, policy, recommendation shaping, reporting. The runtime owns none. The contract between them is a JSON schema (`TrainingRecommendation`), validated at the `hai writeback` boundary.

This framing was not always true. Through 2026-04-16 the repo had Python modules for policy rules, state classification, and recommendation selection. The 2026-04-17 reshape stripped all of that to markdown. See `phase_timeline.md` for the full history.

## 2. How to orient the repo

```
src/health_agent_infra/     # Python — all tools
skills/                      # Markdown — all judgment
reporting/
    docs/                    # controlling doctrine + this tour
    artifacts/flagship_loop_proof/
        2026-04-16-recovery-readiness-v1/   # synthetic proof bundle
        2026-04-16-garmin-real-slice/        # real Garmin CSV proof bundle
safety/tests/                # 14 deterministic + contract tests
pull/data/garmin/export/     # committed CSV the flagship reads
merge_human_inputs/          # README + examples for the intake skill
pyproject.toml               # declares `hai` console_script
```

Rule of thumb: if the file is `.py`, it's a tool. If it's `SKILL.md`, it's a skill. The agent reads skills; tests test tools; docs describe both.

## 3. Where the thesis lives

- [`canonical_doctrine.md`](canonical_doctrine.md) — the controlling thesis. Wins any conflict with other docs.
- [`explicit_non_goals.md`](explicit_non_goals.md) — what this project refuses to build. Load-bearing for scope discipline.

The non-goals doc is the counterweight to every "could we also..." impulse. Re-read it before proposing expansions.

## 4. Where the runtime lives

Six Python modules in `src/health_agent_infra/`:

- `cli.py` — `hai` dispatcher. Every user-visible operation routes through here.
- `pull/garmin.py` — adapter reading the committed Garmin CSV export into PULL dict shape.
- `pull/protocol.py` — `FlagshipPullAdapter` Protocol. Any adapter satisfying the `source_name: str` + `load(as_of) -> dict` signature conforms.
- `clean/recovery_prep.py` — `clean_inputs()` emits `CleanedEvidence`; `build_raw_summary()` emits `RawSummary` (deltas, ratios, counts, coverage fractions — no bands).
- `writeback/recommendation.py` — `perform_writeback()` takes a `TrainingRecommendation`, enforces writeback-locality, appends idempotently.
- `review/outcomes.py` — `schedule_review`, `record_review_outcome`, `summarize_review_history` (counts only).
- `schemas.py` — typed dataclasses for all structured IO. `CleanedEvidence`, `RawSummary`, `TrainingRecommendation`, `PolicyDecision`, `FollowUp`, `ReviewEvent`, `ReviewOutcome`. No classification enums.

If a stage grows unwieldy, split inside its file rather than adding a helper module. The shape of the CLI is the shape of the code.

## 5. Where the judgment lives

Five markdown skills in `skills/`:

- `recovery-readiness/SKILL.md` — the loop's centerpiece. Decision tables for state classification (sleep debt, RHR band, HRV band, load band, coverage, recovery status, readiness score), the six policy rules (R1 coverage, R2 no-diagnosis, R3 bounded-action, R4 review-required, R5 no-high-confidence-on-sparse, R6 RHR-spike-escalate), and the action-selection matrix.
- `reporting/SKILL.md` — narration voice. How to translate a recommendation into plain language without adding judgment.
- `merge-human-inputs/SKILL.md` — partitioning raw human input into dataset slots (subjective recovery, session log, nutrition, context notes).
- `writeback-protocol/SKILL.md` — when to call `hai writeback` / `hai review`, the JSON shapes expected, idempotency.
- `safety/SKILL.md` — hard refusals, fail-closed boundaries, scope edges.

Skills sit in `~/.claude/skills/` after `hai setup-skills` runs. Claude Code discovers them there automatically. Other Claude agent surfaces (Agent SDK, Claude.ai) have their own skill mechanisms — see `agent_integration.md`.

## 6. Where the proof lives

Two captured bundles in `reporting/artifacts/flagship_loop_proof/`:

- `2026-04-16-recovery-readiness-v1/` — 8 synthetic scenarios. Each `captured/*.json` records an end-to-end run: cleaned evidence, raw state, recommendation, writeback, review event, review outcome.
- `2026-04-16-garmin-real-slice/` — the real Garmin CSV flowing through the same pipeline.

**Note:** these captures were produced by the pre-reshape Python runtime. Regenerating them with an agent driving the skills-layer is a follow-on — see `STATUS.md`. The JSON shapes remain instructive; specific values may shift when re-run.

## 7. How to use it

Install:

```bash
pip install -e .
hai setup-skills
```

From the agent's perspective (inside Claude Code):

```bash
hai intake readiness --soreness moderate --energy high --planned-session-type hard --active-goal strength_block > /tmp/mr.json
hai pull --date 2026-04-17 --user-id u_1 --manual-readiness-json /tmp/mr.json > /tmp/evidence.json
hai clean --evidence-json /tmp/evidence.json > /tmp/prep.json
# agent reads /tmp/prep.json + the recovery-readiness skill,
# produces /tmp/rec.json matching TrainingRecommendation
hai writeback --recommendation-json /tmp/rec.json --base-dir ~/.local/share/hai/recovery_readiness_v1
hai review schedule --recommendation-json /tmp/rec.json --base-dir ~/.local/share/hai/recovery_readiness_v1
# next morning:
# agent constructs outcome JSON, then:
hai review record --outcome-json /tmp/outcome.json --base-dir ~/.local/share/hai/recovery_readiness_v1
hai review summary --base-dir ~/.local/share/hai/recovery_readiness_v1
```

## 8. What's intentionally not here

- No ML / learning loop. Confidence doesn't adjust automatically from past outcomes; `summarize_review_history` only counts.
- No second source. Apple Health, Oura, Strava, Whoop all off-limits per non-goals.
- No UI.
- No multi-user.
- No MCP server (yet — deferred; CLI+skills sufficient for current scope).
- No classification enums in schemas. All classification is agent work.

No `TODO(founder)` markers remain in the code tree. Heuristics that pretended to be judgment were stripped in commit 3 of the reshape.

## 9. Reading paths by question

| Question | Start at |
|---|---|
| "What is this project?" | [`canonical_doctrine.md`](canonical_doctrine.md) |
| "Why is the runtime so thin?" | [`canonical_doctrine.md`](canonical_doctrine.md) + the `recovery-readiness` skill in `skills/` |
| "How does the agent decide?" | `skills/recovery-readiness/SKILL.md` |
| "How does my agent install this?" | [`agent_integration.md`](agent_integration.md) |
| "Is it tested?" | `safety/tests/test_recovery_readiness_v1.py` (14 tests, deterministic + contract) |
| "Does it run on real data?" | `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` |
| "How did we get here?" | [`phase_timeline.md`](phase_timeline.md) |
| "What's next?" | `STATUS.md` |
| "Why not UI / cloud / coach / more sources?" | [`explicit_non_goals.md`](explicit_non_goals.md) |

## 10. One honest caveat

This is a personal-use proof. It's not hosted, not multi-user, not clinical, not polished, not monetized. Its audience is an agent (and the founder's own clarity). If a section of the repo stops making sense, the likely cause is that the repo has evolved past this doc — doctrine wins, come back to `canonical_doctrine.md`.
