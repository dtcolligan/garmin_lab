# Docs — index

Current v1 documentation for Health Agent Infra. Start with
``current_system_state.md`` if you need the latest shipped truth;
start with ``architecture.md`` if this is your first architecture read.

The current docs should make one thing obvious: Health Agent Infra is
not a health chatbot. It is a local governed runtime that gives a
shell-capable agent durable state, deterministic interpretation,
bounded write paths, review memory, recovery tooling, and auditable
explanations for personal-health decisions.

For a one-page orientation of the top-level repo layout (what each
top-level directory is, what is active vs historical), see
[`../../REPO_MAP.md`](../../REPO_MAP.md). For a map of `reporting/`
itself (docs / artifacts / plans / experiments), see
[`../README.md`](../README.md).

## Controlling docs

- [`current_system_state.md`](current_system_state.md) — current package
  version, schema head, command count, release posture, and next-cycle
  roles. This is the shortest "what is true now?" document.
- [`architecture.md`](architecture.md) — pipeline diagram,
  code-vs-skill boundary, R-rule / X-rule intro, package layout.
- [`non_goals.md`](non_goals.md) — what v1 refuses to build and
  why (macros-only nutrition, no ML loop, no hosted, etc).
- [`x_rules.md`](x_rules.md) — full X-rule catalogue with
  triggers, tiers, effects, and config keys.
- [`state_model_v1.md`](state_model_v1.md) — table-by-table state
  schema. The migrations themselves at
  `src/health_agent_infra/core/state/migrations/` are the source of
  truth; this doc may lag the latest migration when a release adds
  schema (currently 025 live as of v0.1.15).

## Read by job

| You need to | Read |
|---|---|
| Know what shipped and what is still unproven | [`current_system_state.md`](current_system_state.md) |
| Understand the runtime shape | [`architecture.md`](architecture.md), then [`state_model_v1.md`](state_model_v1.md) |
| Understand why the product exists | [`personal_health_agent_positioning.md`](personal_health_agent_positioning.md), [`memory_model.md`](memory_model.md), [`query_taxonomy.md`](query_taxonomy.md) |
| Operate the package from an agent | [`agent_integration.md`](agent_integration.md), [`agent_cli_contract.md`](agent_cli_contract.md) |
| Inspect why a recommendation changed | [`explainability.md`](explainability.md), [`x_rules.md`](x_rules.md) |
| Check safety and scope boundaries | [`non_goals.md`](non_goals.md), [`privacy.md`](privacy.md), [`recovery.md`](recovery.md) |
| Extend the runtime | [`how_to_add_a_domain.md`](how_to_add_a_domain.md), [`domains/README.md`](domains/README.md), [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md) |

## Current-vs-provenance rule

Docs directly under this directory are intended as current operating
docs unless their header says otherwise. Cycle docs under
`reporting/plans/v0_*/`, launch drafts, and dated review artifacts
are provenance: useful for why a decision happened, not automatically
current product truth. When they disagree, prefer
`current_system_state.md`, generated CLI capabilities, migrations,
and tests.

## Onboarding

- [`tour.md`](tour.md) — 10-minute guided reading tour.
- [`agent_integration.md`](agent_integration.md) — how Claude
  Code / Agent SDK / open equivalents install and drive the
  package.
- [`domains/README.md`](domains/README.md) — "how to add a new
  domain" checklist; reference implementations are the six v1
  domains.
- [`how_to_add_a_domain.md`](how_to_add_a_domain.md) — conceptual
  walk-through for the domain-extension surface; pairs with the
  `domains/README.md` checklist.
- [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md) —
  contract + evidence shape + DoD for adding a second source
  adapter under `core/pull/`.

## Archived

[`archive/doctrine/`](archive/doctrine/) holds pre-rebuild
doctrine docs (canonical_doctrine.md, chief_operational_brief,
founder_doctrine, phase_timeline). They are retained for
historical context only — do not cite them as current truth. See
``archive/doctrine/README.md`` for the supersession map.

## Where proof lives

- Eval runner captures:
  ``reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/``
- Plans (rebuild + Phase 2.5 gates):
  ``reporting/plans/``
- Throwaway prototypes (Phase 0.5, Phase 2.5 Track A/B):
  ``reporting/experiments/``
