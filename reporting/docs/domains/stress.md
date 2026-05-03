# Stress Domain

Stress converts Garmin stress, manual stress, and body-battery trend into a
bounded readiness signal. It prevents the agent from treating sustained high
stress as vague context.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/stress/schemas.py` |
| Classifier | `src/health_agent_infra/domains/stress/classify.py` |
| Policy | `src/health_agent_infra/domains/stress/policy.py` |
| Signals | `src/health_agent_infra/domains/stress/signals.py` |
| Manual intake | `src/health_agent_infra/domains/stress/intake.py` |
| Skill | `src/health_agent_infra/skills/stress-regulation/SKILL.md` |

## Inputs and accepted state

Stress reads wearable stress and body-battery values where available, plus
manual stress observations recorded through `hai intake stress`. Manual input
is a first-class fallback when Garmin stress is absent.

## Classifier output

`ClassifiedStressState` emits:

- `garmin_stress_band`
- `manual_stress_band`
- `body_battery_trend_band`
- `coverage_band`
- `stress_state`
- `stress_score`
- `uncertainty`

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when no usable stress signal is present. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse stress coverage. |
| `sustained_very_high_stress_escalation` | Forces `escalate_for_user_review` when very-high stress persists across the configured window. |

## Action enum

- `maintain_routine`
- `add_low_intensity_recovery`
- `schedule_decompression_time`
- `escalate_for_user_review`
- `defer_decision_insufficient_signal`

## Cross-domain participation

Stress contributes X7 confidence capping and body-battery X6a/X6b rules.
Low body battery can soften hard proposals; depleted body battery can block
hard proposals into user review.

## Skill contract

The stress skill explains the runtime state and can suggest bounded
decompression/recovery actions. It must not infer hidden stress scores,
recalculate body-battery trend, or override sustained-stress escalations.
