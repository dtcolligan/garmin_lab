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
| [`plans/`](plans/) | mixed (one active roadmap + historical phase docs) | The next-cycle roadmap and the launch notes are active; the `phase_*` documents and the skill-harness RFC are historical phase records (gates, findings) preserved for context. |
| [`experiments/`](experiments/) | historical / archived prototypes | Throwaway prototypes from Phase 0.5 and Phase 2.5 that decided whether to commit to specific architectural bets. Frozen as proof of those decisions; **not** living code. See [`experiments/README.md`](experiments/README.md). |

## Active vs historical inside `plans/`

| File | Status |
|---|---|
| [`plans/post_v0_1_roadmap.md`](plans/post_v0_1_roadmap.md) | active — the current cycle plan |
| [`plans/launch_notes.md`](plans/launch_notes.md) | active — describes the shipped `v0.1.0` runtime |
| [`plans/skill_harness_rfc.md`](plans/skill_harness_rfc.md) | active — the Phase E pilot RFC |
| [`plans/phase_0_findings.md`](plans/phase_0_findings.md) | historical — Phase 0 preflight verdict |
| [`plans/phase_0_5_synthesis_prototype.md`](plans/phase_0_5_synthesis_prototype.md) | historical — Phase 0.5 feasibility verdict |
| [`plans/phase_2_5_retrieval_gate.md`](plans/phase_2_5_retrieval_gate.md) | historical — Phase 2.5 Track A retrieval gate |
| [`plans/phase_2_5_independent_eval.md`](plans/phase_2_5_independent_eval.md) | historical — Phase 2.5 Track B independent eval gate |

The phase documents are kept alongside the roadmap on purpose: they
explain *why* the runtime has the shape it does (e.g. why nutrition
is macros-only, why synthesis is a single skill rather than a
multi-agent debate). Treat them as decision history, not a backlog.

## What is intentionally not here

- No runtime code. Anything imported by the wheel lives under
  [`../src/health_agent_infra/`](../src/health_agent_infra/).
- No tests or evals. Those live under
  [`../safety/`](../safety/) (with the eval runner itself packaged
  inside the wheel at `src/health_agent_infra/evals/`).
- No generated outputs. The eval CSVs / SQLite DBs the runtime emits
  during local use go under the gitignored top-level `data/` and
  `artifacts/` directories, not here.
