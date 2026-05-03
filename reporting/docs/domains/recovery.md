# Recovery Domain

Recovery is the readiness anchor for the v1 runtime. It decides whether the
body appears recovered enough for the planned training day, using sleep debt,
resting heart rate, HRV, recent load, and optional soreness self-report.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/recovery/schemas.py` |
| Classifier | `src/health_agent_infra/domains/recovery/classify.py` |
| Policy | `src/health_agent_infra/domains/recovery/policy.py` |
| Manual intake | `src/health_agent_infra/domains/recovery/readiness_intake.py` |
| Skill | `src/health_agent_infra/skills/recovery-readiness/SKILL.md` |

## Inputs and accepted state

Recovery reads accepted daily state derived from wearable sleep/recovery
signals plus optional manual readiness/soreness input. The classifier consumes
today's evidence and a raw summary that includes trend/ratio fields such as
resting-HR ratio, HRV ratio, trailing training load, and resting-HR spike days.

## Classifier output

`ClassifiedRecoveryState` emits:

- `sleep_debt_band`
- `resting_hr_band`
- `hrv_band`
- `training_load_band`
- `soreness_band`
- `coverage_band`
- `recovery_status`
- `readiness_score`
- `uncertainty`

`readiness_score` is `None` when coverage is insufficient.

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when required inputs are missing. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse evidence. |
| `resting_hr_spike_escalation` | Forces `escalate_for_user_review` when consecutive resting-HR spike days cross the threshold. |

When the resting-HR spike rule fires with reason token
`resting_hr_spike_3_days_running`, recovery may carry source-row locators so
future explanation surfaces can point back to the spike evidence.

## Action enum

- `proceed_with_planned_session`
- `downgrade_hard_session_to_zone_2`
- `downgrade_session_to_mobility_only`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## Cross-domain participation

Recovery proposals are training-domain proposals for synthesis. Hard recovery
sessions can be softened or blocked by X1/X6-style readiness rules, and
recovery state contributes adjacent signals to running and strength.

## Skill contract

The recovery skill reads `classified_state` and `policy_result`, honours
`forced_action` and `capped_confidence`, and composes rationale. It must not
recompute readiness bands, resting-HR spike counters, HRV bands, or X-rule
firings.
