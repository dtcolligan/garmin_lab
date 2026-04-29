# reporting/

Non-runtime narrative material for Health Agent Infra. The runtime
itself lives in [`../src/health_agent_infra/`](../src/health_agent_infra/);
nothing under `reporting/` is imported by the package.

This directory has four subdirectories, each with a distinct role.

## Subdirectories

| Path | Class | Role |
|---|---|---|
| [`docs/`](docs/) | active docs (with `archive/` for pre-rebuild doctrine) | The current v1 documentation set: architecture, x-rules, non-goals, state model, tour, extension paths, positioning, query taxonomy, memory model, explainability, grounded-expert scope. Start at [`docs/README.md`](docs/README.md). |
| [`artifacts/`](artifacts/) | active proof + archived bundles | The sole canonical checked-in proof root. Active proof is the multi-domain eval capture under `flagship_loop_proof/`; older single-domain bundles live under `archive/`; the Phase 0 preflight capture is preserved under `phase_0/`. See [`artifacts/README.md`](artifacts/README.md). |
| [`plans/`](plans/) | mixed (active strategy + release history + historical archive) | Current strategic + tactical + eval + success + risks docs at top level; per-cycle audit folders (`v0_1_*`); historical superseded docs under `historical/`; deep strategy reviews under dated subdirs. See [`plans/README.md`](plans/README.md). |
| [`experiments/`](experiments/) | historical / archived prototypes | Throwaway prototypes from Phase 0.5 and Phase 2.5 that decided whether to commit to specific architectural bets. Frozen as proof of those decisions; **not** living code. See [`experiments/README.md`](experiments/README.md). |

## Active vs historical inside `plans/`

| File / dir | Status |
|---|---|
| [`plans/strategic_plan_v1.md`](plans/strategic_plan_v1.md) | active — 12-24 month strategic vision |
| [`plans/tactical_plan_v0_1_x.md`](plans/tactical_plan_v0_1_x.md) | active — release-by-release plan for v0.1.x |
| [`plans/eval_strategy/v1.md`](plans/eval_strategy/v1.md) | active — how correctness is measured |
| [`plans/success_framework_v1.md`](plans/success_framework_v1.md) | active — how project value is measured |
| [`plans/risks_and_open_questions.md`](plans/risks_and_open_questions.md) | active — what could derail + decisions needed |
| [`plans/v0_1_11/`](plans/v0_1_11/) | active — most recent shipped cycle (v0.1.10–v0.1.11 also under their own dirs) |
| [`plans/post_v0_1_10/`](plans/post_v0_1_10/) | active — between-cycles work (demo + Phase 4 audit plans) |
| [`plans/future_strategy_2026-04-29/`](plans/future_strategy_2026-04-29/) | active — Claude/Codex deep strategy review + reconciliation |
| [`plans/historical/`](plans/historical/) | superseded — 9 pre-2026-04-27 planning docs (multi_release_roadmap, post_v0_1_roadmap, agent_operable_runtime_plan, launch_notes, skill_harness_rfc, phase_0_*, phase_2_5_*). Provenance only. |
| [`plans/docs_overhaul/codex_review.md`](plans/docs_overhaul/codex_review.md) | historical — docs-overhaul review record |

Historical plan documents are kept on purpose: they explain *why* the
runtime has the shape it does (e.g. why nutrition is macros-only, why
synthesis is a single skill rather than a multi-agent debate). Treat
them as decision history, not a backlog.

## What is intentionally not here

- No runtime code. Anything imported by the wheel lives under
  [`../src/health_agent_infra/`](../src/health_agent_infra/).
- No tests or evals. Those live under
  [`../verification/`](../verification/) (with the eval runner itself packaged
  inside the wheel at `src/health_agent_infra/evals/`).
- No generated outputs. The eval CSVs / SQLite DBs the runtime emits
  during local use go under the gitignored top-level `data/` and
  `artifacts/` directories, not here.
