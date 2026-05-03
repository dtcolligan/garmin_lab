# Sleep Domain

Sleep evaluates last night's sleep and short-term sleep debt so the agent can
avoid treating poor sleep as a generic note. It is both a direct domain and a
cross-domain readiness signal.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/sleep/schemas.py` |
| Classifier | `src/health_agent_infra/domains/sleep/classify.py` |
| Policy | `src/health_agent_infra/domains/sleep/policy.py` |
| Signals | `src/health_agent_infra/domains/sleep/signals.py` |
| Skill | `src/health_agent_infra/skills/sleep-quality/SKILL.md` |

## Inputs and accepted state

Sleep uses sleep duration, sleep score, awake minutes, timing consistency, and
trailing sleep history. The accepted state is wearable-derived; missing
components propagate as uncertainty rather than guessed values.

## Classifier output

`ClassifiedSleepState` emits:

- `sleep_debt_band`
- `sleep_quality_band`
- `sleep_timing_consistency_band`
- `sleep_efficiency_band`
- `coverage_band`
- `sleep_status`
- `sleep_score`
- `uncertainty`

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when the sleep surface lacks enough evidence. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse sleep evidence. |
| `chronic_deprivation_escalation` | Forces an escalation-style sleep action when the trailing window shows chronic deprivation. |

## Action enum

- `maintain_schedule`
- `prioritize_wind_down`
- `sleep_debt_repayment_day`
- `earlier_bedtime_target`
- `defer_decision_insufficient_signal`

## Cross-domain participation

Sleep debt drives X1a/X1b synthesis behavior. Moderate sleep debt can soften
hard proposals; elevated sleep debt can block hard proposals into user review.
Sleep state also feeds adjacent recovery/running interpretation.

## Skill contract

The sleep skill turns the runtime's sleep bands into practical framing. It must
not recalculate sleep debt, sleep score, efficiency, or chronic-deprivation
windows.
