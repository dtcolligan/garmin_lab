# Health Agent Infra

**Health Agent Infra is a governed runtime and contract layer that turns user-owned health evidence into structured state, so a Claude agent (or open equivalent) can make safe, personally tailored training recommendations.**

It is not a chatbot, a wearable API, a broad AI health app, or a clinical product. It is infrastructure the agent consumes: **deterministic Python tools** that ingest and validate evidence, plus **markdown skills** that instruct the agent in how to classify state, apply policy, and shape recommendations.

- Python = tools (data acquisition, normalization, writeback, schema validation, tests)
- Markdown = skills (judgment: state classification, policy, recommendation, reporting, safety)
- The agent reads skills; the runtime owns no judgment.

## Runtime at a glance

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      user installs `hai` in their terminal               │
└──────────────────────────────────────────────────────────────────────────┘
           │                                                  ▲
           ▼                                                  │
   hai setup-skills  ─── copies skills/ to ~/.claude/skills/  │
                                                              │
┌─────────────┐   hai pull   ┌─────────────────┐              │
│   Garmin    │ ───────────► │  Evidence JSON  │              │
│   CSV       │              │  (raw pull)     │              │
└─────────────┘              └─────────────────┘              │
                                     │                        │
                                     │ hai clean              │
                                     ▼                        │
                       ┌──────────────────────────┐           │
                       │  CleanedEvidence +       │           │
                       │  RawSummary JSON         │────► agent reads this
                       └──────────────────────────┘        plus the
                                                           recovery-readiness
                                                           skill, produces a
                                                           TrainingRecommendation
                                                           JSON
                                                              │
                                ┌─────────────────────────────┘
                                ▼
                       ┌──────────────────────┐
                       │  hai writeback       │ ◄── schema-validates the
                       │  (recommendation)    │     agent's JSON before
                       └──────────────────────┘     persisting. This is
                                │                    the determinism
                                ▼                    boundary.
                       ┌──────────────────────┐
                       │  recommendation_log  │
                       │  .jsonl + daily_plan │
                       │  markdown note       │
                       └──────────────────────┘
                                │
                                ▼
                       ┌──────────────────────┐
                       │  hai review schedule │── logs next-morning
                       │  hai review record   │   review event + outcome
                       │  hai review summary  │── counts by category
                       └──────────────────────┘
```

## Install

```bash
pip install -e .                # or pip install health_agent_infra after publish
hai setup-skills                # copies skills/ to ~/.claude/skills/
hai --help
```

`hai` exposes these subcommands:

```
hai intake readiness --soreness low|moderate|high --energy low|moderate|high \
                     --planned-session-type <text> [--active-goal <text>] [--as-of <date>]
hai pull      --date 2026-04-17 [--manual-readiness-json mr.json | --use-default-manual-readiness]
hai clean     --evidence-json evidence.json
hai writeback --recommendation-json rec.json --base-dir <writeback_root>
hai review    schedule --recommendation-json rec.json --base-dir <root>
hai review    record   --outcome-json outcome.json --base-dir <root>
hai review    summary  --base-dir <root> [--user-id u_local_1]
hai setup-skills [--dest ~/.claude/skills] [--force]
```

The writeback root must end in `recovery_readiness_v1/` — enforced at the I/O boundary.

## Read this repo in 3 minutes

1. **Thesis and runtime model** — [reporting/docs/canonical_doctrine.md](reporting/docs/canonical_doctrine.md)
2. **Reading tour** — [reporting/docs/tour.md](reporting/docs/tour.md) (10-minute guided walkthrough)
3. **How an agent integrates** — [reporting/docs/agent_integration.md](reporting/docs/agent_integration.md)
4. **Inspect one captured synthetic scenario** — `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/captured/recovered_with_easy_plan.json`
5. **Inspect the real Garmin slice** — `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/captured/real_garmin_slice_2026-04-08.json`

## Scope

- **Controlling doctrine**: [reporting/docs/canonical_doctrine.md](reporting/docs/canonical_doctrine.md).
- **Explicit non-goals**: [reporting/docs/explicit_non_goals.md](reporting/docs/explicit_non_goals.md).
- **Phase timeline** (how we got here): [reporting/docs/phase_timeline.md](reporting/docs/phase_timeline.md).
- **Executed reshape plan**: `/Users/domcolligan/.claude/plans/eventual-weaving-pnueli.md`.
- **How to contribute**: [CONTRIBUTING.md](CONTRIBUTING.md).

## Repo layout

```
health_agent_infra/
├── src/health_agent_infra/            # installable package
│   ├── cli.py                         # `hai` dispatcher
│   ├── validate.py                    # code-enforced invariants (9 ids)
│   ├── schemas.py                     # typed dataclasses (the agent's contract)
│   ├── pull/                          # Garmin adapter + flagship Protocol
│   ├── clean/                         # evidence validation + raw-number aggregation
│   ├── writeback/                     # schema-validated local persistence
│   ├── review/                        # event + outcome persistence, summary counts
│   ├── skills/                        # markdown skills packaged with the wheel
│   │   ├── recovery-readiness/SKILL.md    # state classification + policy + shaping
│   │   ├── reporting/SKILL.md             # narration voice
│   │   ├── merge-human-inputs/SKILL.md    # partitioning raw human input
│   │   ├── writeback-protocol/SKILL.md    # when/how to invoke hai writeback
│   │   └── safety/SKILL.md                # fail-closed boundaries
│   └── data/garmin/export/            # committed offline CSV export used by `hai pull`
├── reporting/
│   ├── docs/                          # doctrine, tour, timeline, flagship spec
│   └── artifacts/
│       └── flagship_loop_proof/
│           ├── 2026-04-16-recovery-readiness-v1/   # synthetic 8-scenario bundle
│           └── 2026-04-16-garmin-real-slice/        # real Garmin CSV bundle
├── safety/tests/                      # deterministic + contract tests
├── merge_human_inputs/                # README + examples for the intake skill
├── pyproject.toml                     # declares `hai` console_script
├── README.md, STATUS.md, CONTRIBUTING.md
└── LICENSE
```

## What is proven now

- `hai intake readiness` emits a validated manual-readiness JSON (enum-checked `soreness` and `energy`) that composes with `hai pull --manual-readiness-json`.
- `hai pull` reads the committed Garmin CSV export and emits evidence JSON.
- `hai clean` computes CleanedEvidence + RawSummary deterministically — no bands, no classifications, no scores.
- `hai writeback` schema-validates an agent-produced TrainingRecommendation and persists it idempotently, with writeback-locality enforced at the I/O boundary.
- `hai review schedule/record/summary` covers the review loop.
- 14 tests passing covering deterministic tooling + contract validation.
- 8 synthetic captured scenarios + 1 real Garmin slice under `reporting/artifacts/flagship_loop_proof/`.

## Not claimed

- Not a clinical product or medical device.
- Not hosted or multi-user.
- Not a polished general-user install flow.
- Not a learning loop — the runtime holds no ML model.
- Not a source-fusion platform — the flagship only consumes Garmin + typed manual readiness. Broader multi-source merging is out of scope for this interval.

## Phase 6 reshape — 2026-04-17

The repo was reshaped from a self-contained Python implementation of the flagship loop into a tools-plus-skills package an agent can install and consume. Seven commits:

1. Delete obvious legacy (archive, research notebooks, older Garmin extractors, gray-area connector dirs).
2. Move surviving runtime into `src/health_agent_infra/` installable layout.
3. Strip runtime judgment — policy, state classification, recommendation shaping became skill markdown. The agent owns all classification.
4. Sweep older CLI chain (`agent_*_cli.py`), compat wrappers, data-layer modules, their tests.
4c. Sweep older proof bundles and legacy doctrine docs.
5. Docs refresh + install story (this commit).

See `reporting/docs/phase_timeline.md` for the full history.
