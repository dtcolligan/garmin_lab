# Glossary

Short definitions for project terms that recur across the docs. Prefer these
terms consistently; link to the canonical doc when a term needs more detail.

| Term | Meaning | Canonical surface |
|---|---|---|
| accepted state | Per-domain daily state after raw evidence has been projected into canonical tables. | `state_model_v1.md` |
| adapted recommendation | The final recommendation after synthesis and X-rule mutations. | `explainability.md` |
| agent-native | Designed for a shell-capable agent to operate directly through a typed CLI contract, not for a human-only GUI. | `agent_integration.md` |
| agent-safe | A command the agent may call when user intent and preconditions are satisfied. Agent-safe does not mean ungated or unvalidated. | `agent_cli_contract.md` |
| bounded | The action is drawn from a fixed schema/enum and validated before persistence. | `architecture.md` |
| capped_confidence | A policy result that lowers the maximum confidence a skill may emit, usually on sparse evidence. | `domains/README.md` |
| classified_state | Deterministic per-domain bands, scores, status, coverage, and uncertainty tokens. | `architecture.md` |
| coverage_band | The classifier's evidence sufficiency label: full, partial, sparse, or insufficient. | `domains/README.md` |
| data_quality_daily | Snapshot-visible table for per-domain coverage, missingness, source-unavailable, user-input-pending, and cold-start state. | `state_model_v1.md` |
| deterministic boundary | A CLI/runtime point that validates and rejects invalid state transitions before writes. | `agent_integration.md` |
| DomainProposal | The per-domain object a skill submits through `hai propose`; it is validated before entering `proposal_log`. | `domains/README.md` |
| evidence locator | Structured pointer back to source rows that justified a firing or future evidence card. | `state_model_v1.md` |
| forced_action | A policy result that fixes the action a skill must use. | `domains/README.md` |
| host agent | The LLM agent operating the local CLI. Claude Code is the first compatible host, not the product boundary. | `agent_integration.md` |
| ingest_actor | The actor that transported a row into local state, distinct from the upstream source. | `how_to_add_a_pull_adapter.md` |
| local governance | The runtime, database, migrations, policy, and commit path live on the user's machine and constrain what the model can do. | `personal_health_agent_positioning.md` |
| Phase A | Synthesis rules that run over snapshot + proposals before final recommendation commit. | `x_rules.md` |
| Phase B | Post-adjustment synthesis rules that may only mutate allowed detail fields after drafts exist. | `x_rules.md` |
| planned recommendation | The pre-X-rule aggregate recommendation captured before synthesis mutates drafts. | `explainability.md` |
| policy_result | Per-domain mechanical R-rule output: decisions, forced action, confidence cap, and detail payload. | `architecture.md` |
| R-rule | Per-domain mechanical policy rule implemented in `domains/<d>/policy.py`. | `domains/README.md` |
| source freshness | Runtime knowledge about when each data source last synced and whether the data came from live or fixture sources. | `current_system_state.md` |
| supersession | Versioning path that preserves old rows while pointing to the newer canonical row. | `state_model_v1.md` |
| target_status | Nutrition target availability state: present, absent, or unavailable. | `architecture.md` |
| USER_INPUT | Exit-code class for caller-fixable preconditions, bad flags, missing user-supplied state, or governed refusals. | `cli_exit_codes.md` |
| W57 | Governance invariant: an agent cannot activate/deactivate user intent or target rows without explicit user commit/archive authority. | `AGENTS.md` |
| X-rule | Cross-domain synthesis rule implemented in `core/synthesis_policy.py`. | `x_rules.md` |
