# Minimal Policy Rules — v1

Status: Phase 1 doctrine. Adopted 2026-04-16. Derived from [canonical_doctrine.md](canonical_doctrine.md) and [flagship_loop_spec.md](flagship_loop_spec.md).

Policy must be executable, not prose. This document is the v1 rule set the POLICY layer enforces for the flagship loop. Each rule has a stable `rule_id`, a precise trigger, a decision, and an audit expectation. The set is intentionally small: the goal is a credible minimum, not a complete safety framework.

## Decisions

Each rule evaluates to one decision:

- `allow` — the recommendation may proceed as constructed
- `soften` — the recommendation is permitted but one or more fields (usually `confidence` or `action`) are downgraded
- `block` — the recommendation is not emitted; a `defer_decision_insufficient_signal` is emitted instead
- `escalate` — the recommendation includes an escalation action for user attention

All fired decisions are captured in `training_recommendation.policy_decisions`.

## Rules

### R1 — `require_min_coverage`

Trigger: always runs.

Behavior:

- if `recovery_state.signal_quality.coverage == "insufficient"` -> `block`
- else -> `allow`

Purpose: refuse to produce a substantive recommendation when the required input set is not present.

### R2 — `no_high_confidence_on_sparse_signal`

Trigger: always runs.

Behavior:

- if `recovery_state.signal_quality.coverage == "sparse"` and proposed `confidence == "high"` -> `soften` to `moderate`
- else -> `allow`

Purpose: prevent the system from sounding confident when evidence is thin.

### R3 — `no_diagnosis`

Trigger: always runs.

Behavior:

- if proposed `rationale` or `action_detail` contains any diagnosis-shaped language (closed vocabulary list to be enforced in code) -> `block`
- else -> `allow`

Purpose: categorical constraint. The system is not a clinical product. It does not name conditions.

### R4 — `resting_hr_spike_escalation`

Trigger: `recovery_state.resting_hr_vs_baseline == "well_above"` for 3 or more consecutive days based on state history.

Behavior:

- `escalate` — emit `action = escalate_for_user_review` with `action_detail.reason_token = "resting_hr_spike_3_days_running"`

Purpose: a persistent resting-HR spike is a pattern worth surfacing even though the system does not diagnose.

### R5 — `bounded_action_envelope`

Trigger: always runs.

Behavior:

- if proposed `action` is not in the closed v1 action enum defined in [recommendation_object_schema.md](recommendation_object_schema.md) -> `block`
- else -> `allow`

Purpose: keep the action surface explicitly enumerated. New actions require a schema change, not prose.

### R6 — `writeback_locality`

Trigger: evaluated by the ACTION layer before writing.

Behavior:

- if the proposed writeback targets anything other than local recommendation log or local daily plan note -> `block`
- else -> `allow`

Purpose: this phase allows only local, reversible writebacks. No external service writes.

### R7 — `review_required`

Trigger: always runs.

Behavior:

- if `training_recommendation.follow_up` is missing, empty, or references a `review_at` outside the next 24 hours -> `block`
- else -> `allow`

Purpose: every emitted recommendation must carry a review event. A loop without review is not agentic.

## Evaluation order

1. R1 `require_min_coverage`
2. R3 `no_diagnosis`
3. R5 `bounded_action_envelope`
4. R7 `review_required`
5. R2 `no_high_confidence_on_sparse_signal`
6. R4 `resting_hr_spike_escalation`
7. R6 `writeback_locality` (runs in ACTION layer, not RECOMMEND layer)

Rules 1, 3, 5, 7 are gates that can `block`. Rule 2 is a softener. Rule 4 converts to `escalate`. Rule 6 sits in ACTION.

## Audit expectations

For every run of the flagship loop:

- every rule that fires records one entry in `training_recommendation.policy_decisions`
- the audit log is deterministic given the same `recovery_state` and proposed recommendation
- rules that did not need to fire (for example R4 when history does not match) do not emit entries

## Implementation expectations

Policy code lives in the `safety/` bucket (POLICY layer in runtime terms). At minimum:

- each rule is a named, unit-tested function
- inputs are typed objects, not free dicts
- rule identifiers match the `rule_id` strings in this doc
- the rule set is exposed as a single ordered evaluator so the audit log is consistent

## Intentional non-coverage

This rule set is deliberately small. It does not attempt to cover nutrition, medication, mental health, environmental factors, or populations outside the current single-user scope. Expansion of the rule set is Phase 4 work and must be accompanied by schema versioning.

## Related

- [canonical_doctrine.md](canonical_doctrine.md)
- [flagship_loop_spec.md](flagship_loop_spec.md)
- [state_object_schema.md](state_object_schema.md)
- [recommendation_object_schema.md](recommendation_object_schema.md)
- [explicit_non_goals.md](explicit_non_goals.md)
