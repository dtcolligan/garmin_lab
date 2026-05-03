# Health Agent Infra

Health Agent Infra is a locally governed runtime for personal health
agents.

You talk to an agent. The agent invokes the local `hai` CLI. The
runtime defines and enforces what the agent is allowed to do. It is
the boundary that lets an LLM work over personal health data without
owning the policy engine, the database, or the final write path.

The package is working single-user software. It is currently packaged
and tested around Claude Code as the first compatible agent surface,
but the core contract is a local CLI plus machine-readable capability
manifest, not a Claude-only backend.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2631_passing-green)](verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this exists

Agentic AI in health fails when the agent is asked to be everything at
once: chat interface, memory layer, data interpreter, planner,
database writer, validator, and auditor.

That breaks down in predictable ways:

| Failure mode | What goes wrong |
|---|---|
| No durable health state | The agent forgets context, re-asks for data already provided, or reasons from a partial chat window. |
| Non-deterministic interpretation | The same wearable data or self-report can be interpreted differently from run to run. |
| Unsafe write path | The agent can blur the line between proposing a change and mutating the user's state. |
| Weak validation | Plans are generated as prose before the system proves that required evidence and constraints are present. |
| Opaque recommendations | The user cannot reconstruct why a recommendation changed after sleep, stress, nutrition, or training load shifted. |
| No review loop | The system does not reliably learn whether yesterday's recommendation was followed or useful. |

Health Agent Infra fixes those failure modes by moving the durable,
deterministic, and auditable parts into local software. The LLM stays
where it is strongest: conversation, clarification, summarisation, and
domain-specific rationale over a bounded state surface.

## What the product does

Health Agent Infra maintains a local SQLite health-state database. It
pulls wearable data, accepts manual intake, projects everything into
typed daily state, classifies each domain, applies deterministic policy
rules, lets the agent propose bounded actions, and commits the final
plan through an auditable transaction.

In practice:

1. You converse with the agent about training, recovery, sleep,
   nutrition, stress, and missing context.
2. The agent reads `hai capabilities --json` to understand exactly
   which commands are safe and what each command can mutate.
3. `hai` pulls or records evidence and maintains the local health-state
   database.
4. Python code interprets the data with deterministic classifiers,
   policy rules, validation, and cross-domain X-rules.
5. Markdown skills help the agent explain uncertainty, ask better
   questions, and write rationale.
6. The runtime, not the LLM, performs the final state write.

The core rule:

> The agent can propose and explain; the runtime validates and commits.

## Where the product stands

The current published package is `health-agent-infra==0.1.15.1`
from 2026-05-03. It is the v0.1.15 foreign-user-ready package plus a
Linux keyring hotfix.

| Area | Current state |
|---|---|
| Daily loop | Working and dogfooded: pull, clean, snapshot, gap detection, proposal gate, synthesis, `hai today`. |
| Health-state database | Local SQLite, 25 migrations, six accepted-state domains, audit rows for proposals/plans/reviews. |
| Wearable input | intervals.icu preferred; Garmin live is supported but marked unreliable; CSV fixture for demos/tests. |
| Manual intake | Readiness, gym, nutrition macros, stress, notes, targets, intent/training rows. |
| Agent contract | 60 annotated commands with mutation class, idempotency, JSON mode, exit codes, and agent-safety metadata. |
| Review loop | `hai review record` and `hai review summary` persist outcomes and re-link through superseded plans. |
| Weekly review | Not shipped as a product loop yet; v0.2.0 is planned to build weekly review on existing provenance rows. |
| Planning | Daily planning works; longer-horizon planning is deliberately constrained and staged behind future review/evidence substrate. |
| External validation | PyPI package published; recorded non-maintainer session pending as empirical validation feeding v0.1.16. |

For the terse release-truth map, read
[`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md).

## The loops this enables

Health Agent Infra is infrastructure around a health-state database.
The loops are the product surface it enables for an agent.

### Daily loop

Current and working. The agent can help plan today by pulling wearable
data, asking for missing self-report, checking readiness, generating
bounded domain proposals, and committing one audited daily plan.

### Review loop

Current and working. The user records whether yesterday's
recommendation was followed and whether it helped. Review outcomes are
stored locally and linked back to the canonical recommendation even
when the day was re-authored.

### Target and planning loop

Partially current. The runtime can store governed targets and intent
rows, including nutrition macro targets, but it does not let the agent
silently activate user-state changes. Agent-proposed targets still
require explicit user commit.

### Weekly review loop

Planned. The database already preserves the evidence needed for a
weekly review: source rows, accepted daily state, proposals, X-rule
firings, recommendations, and outcomes. v0.2.0 is planned to turn
that substrate into a weekly review surface.

### Longer-horizon planning

Future. The project is deliberately building daily state, review
memory, and evidence provenance before giving an agent broader
planning authority.

## How it feels to use

```text
User:  "Plan today. I slept badly and my quads are sore."
Agent: Reads `hai capabilities`, pulls wearable data, asks for missing context.
hai:   Updates the local health-state database and classifies six domains.
Agent: Uses the skills to explain uncertainty and post bounded proposals.
hai:   Applies deterministic cross-domain rules and commits the daily plan.
User:  "Why did you soften the run?"
Agent: Runs `hai explain --operator` and answers from persisted rows.
```

The user experience is conversational. The system architecture is not.
The agent talks; the runtime governs.

## Why it is different

- **Local state, not chat memory.** The system maintains a structured
  health-state database instead of asking the LLM to remember health
  history inside a conversation.
- **Deterministic interpretation.** Wearable data and manual intake
  are projected into typed state before recommendations are made.
- **Validated write path.** The agent cannot bypass the CLI contract
  to mutate state directly.
- **Code and skills have separate jobs.** Python owns bands, R-rules,
  X-rules, validation, supersession, and commits. Markdown skills own
  explanation, uncertainty, and clarification.
- **Agent-native contract.** `hai capabilities --json` tells the agent
  exactly which commands exist, what they can mutate, and whether they
  are agent-safe.
- **Auditable by construction.** Use `hai today`,
  `hai explain --operator`, `hai doctor`, and `hai stats` instead of
  raw SQLite as the first inspection path; these commands resolve
  supersession chains and schema churn.

## Install

The intended interface is an agent, but these are normal CLI commands.

```bash quickstart
# First-install canonical, including the brief PyPI CDN-cache bypass:
pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.15.1'
# OR for a dev checkout: pip install -e .
hai init
hai auth intervals-icu
hai capabilities --human
hai doctor
hai daily
hai today
```

After the immediate post-publish window, the plain install also works:

```bash
pipx install health-agent-infra
```

`intervals_icu` is the preferred live source. Garmin Connect support is
best-effort because Garmin login is rate-limited and can fail behind
Cloudflare; use `--source garmin_live` only when you explicitly want
that path. If no live credentials are configured, the runtime can use
the committed CSV fixture for demos and smoke tests.

On macOS, credentials use the OS keychain. On Linux, v0.1.15.1 includes
`keyrings.alt` and a defensive fallback so setup/status commands do not
crash when no desktop keyring backend is registered.

## Daily workflow

`hai daily` is the current product loop. It runs the runtime-owned
part of the day and tells the agent what still needs to happen.

1. `pull` fetches evidence and records sync freshness.
2. `clean` normalizes evidence into typed accepted-state rows.
3. `snapshot` builds the six-domain state bundle.
4. `gaps` reports missing user-closeable inputs.
5. `proposal_gate` reports whether proposals are still needed.

When proposals are needed, the agent uses the domain skills and writes
one bounded `DomainProposal` per expected domain with `hai propose`.
Then `hai daily` or `hai synthesize` completes the atomic commit.

The full integration contract is in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Reading your plan

`hai today` is the user-facing read surface for the committed daily
plan:

```bash
hai today
hai today --as-of 2026-04-23
hai today --domain recovery
hai today --format json
```

For dense audit output:

```bash
hai explain --operator
```

`hai explain` reconstructs the plan from persisted rows. It does not
recompute the day from scratch.

## Recording your day

The review loop records whether the recommendation was followed and
whether it helped:

```bash
hai review record --outcome-json <path>
hai review summary
hai review summary --domain recovery
```

Review rows are append-only. If you record an outcome against a
morning plan and later re-author the day, the outcome is routed to the
canonical leaf recommendation for the same domain. `followed_recommendation`
and `self_reported_improvement` must be strict booleans.

## Domains

The current runtime covers six daily domains:

| Domain | What it covers |
|---|---|
| recovery | HRV/RHR readiness, soreness, energy, recovery constraints |
| running | recent activities, load, ACWR, session readiness |
| sleep | duration, debt, deprivation risk, recovery interaction |
| stress | self-report and stress trend signals |
| strength | gym set intake, exercise taxonomy, volume spikes |
| nutrition | daily macro totals and target-aware suppression |

Nutrition is daily macros-only in v1, not meal-level tracking. Body
composition, micronutrients, clinical claims, and autonomous diet
plans are intentionally out of scope.

## Calibration

A fresh install can produce recommendations on day one, but useful
personal calibration takes history.

| Window | What to expect |
|---|---|
| Days 1-14 | Cold-start mode for running, strength, and stress. Review recommendations consciously. |
| Day 14 | HRV and RHR rolling baselines begin to stabilize. |
| Days 14-28 | Recovery, sleep, and stress trend signals become more useful. |
| Day 28 | ACWR chronic load and strength volume ratios stop being mechanically inflated. |
| Day 60+ | Trend bands start carrying real signal. |
| Around day 90 | Steady-state personal calibration. |

Cold-start relaxation is asymmetric by design: running, strength, and
stress can soften some coverage blocks; recovery, sleep, and nutrition
do not relax into confident guesses when evidence is thin.

## Where your data lives

| What | Default path | Override |
|---|---|---|
| State DB | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB`, `--db-path` |
| Intake/proposal JSONL | `~/.health_agent/` | `$HAI_BASE_DIR`, `--base-dir` |
| Config | macOS: `~/Library/Application Support/hai/`; Linux: `~/.config/hai/` | `hai config init --path <p>` |

Run `hai doctor` to confirm resolved paths, schema version, source
freshness, credential status, and skill installation.

## First-run notes

- `hai today` needs a committed plan. If there is no plan yet, run
  `hai daily`.
- If `hai daily` stops at `awaiting_proposals`, the agent still needs
  to post bounded domain proposals.
- `hai doctor --deep` performs live API checks; plain `hai doctor`
  checks local setup and credential presence.
- Garmin live is explicitly less reliable than intervals.icu.
- USER_INPUT exits should include the next action. If one does not,
  that is a bug.

## Main command groups

```bash
# Evidence and daily orchestration
hai pull [--source intervals_icu|garmin_live|csv] --date <d>
hai clean --evidence-json <p>
hai daily [--domains <csv>]

# Proposals and synthesis
hai propose --domain <d> --proposal-json <p>
hai synthesize --as-of <d> --user-id <u>
hai synthesize --bundle-only

# State and audit
hai today
hai explain --for-date <d> --user-id <u>
hai state init | migrate | read | snapshot | reproject
hai doctor | stats | capabilities

# Intake, review, targets
hai intake gym|exercise|nutrition|stress|note|readiness ...
hai review schedule | record | summary
hai target set | nutrition | list | archive
```

The authoritative command surface is generated at
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md)
and from `hai capabilities --json`.

## Roadmap and proof

- [ROADMAP.md](ROADMAP.md) - now, next, later.
- [AUDIT.md](AUDIT.md) - release audit index.
- [CHANGELOG.md](CHANGELOG.md) - public release history.
- [`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md) - current shipped truth.
- [`reporting/docs/architecture.md`](reporting/docs/architecture.md) - full architecture.
- [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) - scope boundaries.
- [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) - cross-domain rule catalogue.
- [`reporting/docs/tour.md`](reporting/docs/tour.md) - 10-minute reading tour.

## License

MIT. See [LICENSE](LICENSE).
