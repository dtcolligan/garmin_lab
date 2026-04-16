# Canonical Doctrine

Status: Phase 1 doctrine. Adopted 2026-04-16 per the Chief Operational Brief.

This document is the controlling explanation of what Health Lab is, what it is trying to prove right now, and how the runtime is shaped. It supersedes prior improvised descriptions. If another doc conflicts with this one, this one wins until explicitly retired by a later dated doctrine update.

## Thesis

Health Lab is the governed runtime that turns user-owned health evidence into structured state, making safe, personally tailored agent action possible.

The emphasis is intentional:

- **governed** — the runtime is constrained by an explicit, inspectable policy layer, not by vibes
- **user-owned health evidence** — inputs are the user's own data, pulled from sources the user already controls
- **structured state** — the system exposes a typed, inspectable state object, not prose
- **safe, personally tailored agent action** — outputs are bounded, confidence-expressed, and reversible

Health Lab is not a clinical product, not a hosted multi-user service, not a broad AI health app, and not a medical-grade decision system. It is a governed runtime, proved through one narrow loop.

## Controlling rule: proof before breadth

Near-term project quality will be determined far more by one convincing end-to-end loop than by many connectors, many ideas, or many folders.

Operationally:

- one flagship loop before platform expansion
- one strong connector slice before connector sprawl
- one explicit state model before broad recommendation logic
- one bounded action pathway before richer automation
- one public proof before ambitious narrative inflation

Every proposed change is evaluated against one question:

**Does this make the flagship proof more real, more inspectable, or more legible?**

If not, it is a distraction and should be deferred.

## Runtime architecture

The canonical runtime model is:

```
PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
```

This is the conceptual operating shape of the system. The eight-bucket repo model is preserved as a workstream organisation layer, not as the deepest runtime architecture.

### Layer definitions

#### PULL
Acquires raw evidence from external sources and manual inputs. Outputs raw, source-shaped records. Does not interpret, normalize, or judge.

#### CLEAN
Normalizes, validates, deduplicates, and aligns evidence into canonical, typed objects. Outputs cleaned evidence ready for state construction. Does not recommend.

#### STATE
Constructs the live user state from cleaned evidence, recent history, profile context, and explicit uncertainty accounting. Outputs a typed state object that downstream layers read. State is first-class and visible.

#### POLICY
Constrains what the system may conclude, recommend, or do. Enforces: no diagnosis, no overconfident claims on noisy proxy data, no recommendation when missingness is too high, explicit escalation / no-escalation. Policy is executable, not prose.

#### RECOMMEND
Produces bounded, structured, state-conditioned recommendations. Each recommendation carries action, rationale, confidence, uncertainty, follow-up. No free-form paragraphs as the primary output.

#### ACTION
Executes low-risk approved actions or writebacks under policy. Examples: write a recommendation log entry, append to a daily plan note. ACTION is reversible and auditable. High-risk actions are not in scope.

#### REVIEW
Evaluates outcomes and updates memory / pattern understanding. A loop without review is not agentic; it is only a one-shot response.

### Layer -> bucket mapping

The eight-bucket repo model remains the workstream organisation. The runtime layers map onto it as follows:

- `pull/` -> PULL
- `clean/` -> CLEAN
- `merge_human_inputs/` -> PULL (human evidence) and STATE update surface
- `interpretation/` -> RECOMMEND
- `writeback/` -> ACTION and STATE persistence
- `safety/` -> POLICY
- `reporting/` -> proof and output surfaces for all layers
- `research/` -> exploratory support, outside the runtime

This mapping is interpretive. Sub-namespaces inside a bucket (for example `clean/health_model/`) are implementation locations within that bucket's runtime role, not new canonical categories.

## Scope doctrine

### In scope for this phase

- the flagship recovery and training-readiness loop
- Garmin as the passive-data anchor
- typed manual readiness intake as the human-input anchor
- one explicit state object
- one minimal executable policy layer
- one bounded recommendation object
- one low-risk writeback
- one next-day review event
- public proof surfaces documenting the above

### Out of scope for this phase

See [explicit_non_goals.md](explicit_non_goals.md) for the enforced list. Summary: no second connector before flagship proof, no broad AI health coaching, no medical-style outputs, no rich UI, no deep nutrition system, no speculative MCP expansion.

## Doctrine on abstraction

The language of the project must not run ahead of the implementation. Every major claim in repo-facing language must be backed by a concrete, inspectable artifact. If a claim cannot be traced to code, a schema, or a checked-in proof artifact, the claim is removed or softened until it can be.

## Doctrine on state

State is first-class. The system does not rely on implicit state buried in prose, logs, or chain-of-thought. The state object is typed, versioned, inspectable, and the single input to the recommendation layer.

## Doctrine on policy

Policy is executable. At least one minimal policy rule set must run as code and be test-covered. Prose-only safety claims do not count.

## Doctrine on review

The flagship loop is not complete without a review event. A system that recommends but never asks whether the recommendation helped is not yet an agentic loop.

## Doctrine on legibility

Explanation is product work, not marketing garnish. A smart outsider should be able to understand the project and see why it matters in under two minutes of reading. If the repo cannot be read quickly by a stranger, the work is not yet done.

## Five operating directives

When tradeoffs arise, these dominate in this order:

1. **Conceptual discipline** — words match implementation
2. **Narrowness** — one loop, not many
3. **Inspectability** — state and policy are visible
4. **Boundedness** — actions are low-risk and reversible
5. **Legibility** — an outsider gets it fast

## Links

- [chief_operational_brief_2026-04-16.md](chief_operational_brief_2026-04-16.md)
- [flagship_loop_spec.md](flagship_loop_spec.md)
- [state_object_schema.md](state_object_schema.md)
- [recommendation_object_schema.md](recommendation_object_schema.md)
- [minimal_policy_rules.md](minimal_policy_rules.md)
- [explicit_non_goals.md](explicit_non_goals.md)
