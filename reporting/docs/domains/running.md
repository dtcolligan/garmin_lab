# Running Domain

Running decides whether today's planned run is appropriate given recent running
load, freshness, hard-session density, and adjacent recovery signals.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/running/schemas.py` |
| Classifier | `src/health_agent_infra/domains/running/classify.py` |
| Policy | `src/health_agent_infra/domains/running/policy.py` |
| Signals | `src/health_agent_infra/domains/running/signals.py` |
| Skill | `src/health_agent_infra/skills/running-readiness/SKILL.md` |

## Inputs and accepted state

Running uses daily running rollups plus per-session `running_activity` rows
when available. It also consumes adjacent recovery signals such as training
readiness, sleep debt, and resting-HR band so the running decision is not made
in isolation.

## Classifier output

`ClassifiedRunningState` emits:

- `weekly_mileage_trend_band`
- `hard_session_load_band`
- `freshness_band`
- `recovery_adjacent_band`
- `coverage_band`
- `running_readiness_status`
- `readiness_score`
- `uncertainty`

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when required running signals are missing. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse coverage. |
| `acwr_spike_escalation` | Forces `escalate_for_user_review` when acute:chronic workload ratio reaches the spike threshold. |

## Action enum

- `proceed_with_planned_run`
- `downgrade_intervals_to_tempo`
- `downgrade_to_easy_aerobic`
- `cross_train_instead`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## Cross-domain participation

Running is a training domain. It can be softened or blocked by sleep debt,
nutrition underfuelling, recovery load spikes, body-battery depletion, and
strength sequencing rules. A hard running draft may also cause X9 to adjust a
nutrition draft's protein-target detail.

## Skill contract

The running skill chooses from the running action enum and explains uncertainty
using already-computed bands. It must not calculate ACWR, mileage trends,
freshness, sleep debt, or synthesis effects in markdown.
