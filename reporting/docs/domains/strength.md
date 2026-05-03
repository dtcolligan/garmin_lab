# Strength Domain

Strength evaluates recent resistance-training volume, muscle-group freshness,
exercise taxonomy confidence, and unmatched exercise tokens. It exists because
strength intake is structurally richer than a free-text workout note.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/strength/schemas.py` |
| Classifier | `src/health_agent_infra/domains/strength/classify.py` |
| Policy | `src/health_agent_infra/domains/strength/policy.py` |
| Signals | `src/health_agent_infra/domains/strength/signals.py` |
| Intake | `src/health_agent_infra/domains/strength/intake.py` |
| Taxonomy match | `src/health_agent_infra/domains/strength/taxonomy_match.py` |
| Skill | `src/health_agent_infra/skills/strength-readiness/SKILL.md` |

## Inputs and accepted state

Strength reads structured gym-session and gym-set rows, canonical exercise
taxonomy entries, muscle-group mapping, and recent volume history. `hai intake
gym` and the strength-intake skill turn user narration into structured sets.

## Classifier output

`ClassifiedStrengthState` emits:

- `recent_volume_band`
- `freshness_band_by_group`
- `coverage_band`
- `strength_status`
- `strength_score`
- `volume_ratio`
- `unmatched_exercise_tokens`
- `uncertainty`

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when the strength surface lacks enough structured evidence. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse coverage. |
| `volume_spike_escalation` | Forces `escalate_for_user_review` when recent volume ratio reaches the spike threshold and history is sufficient. |
| `unmatched_exercise_confidence_cap` | Caps confidence when unmatched exercise tokens are present. |

## Action enum

- `proceed_with_planned_session`
- `downgrade_to_technique_or_accessory`
- `downgrade_to_moderate_load`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## Cross-domain participation

Strength is a training domain. Hard strength drafts can be softened or blocked
by sleep debt, nutrition underfuelling, body battery, and recovery signals.
Yesterday's hard run can soften lower-body strength, and yesterday's heavy
lower-body strength can soften today's running.

## Skill contract

The strength skill reads structured state and policy output. It can choose a
bounded action and explain uncertainty, but taxonomy matching, volume ratios,
muscle-group freshness, and unmatched-token confidence caps belong in code.
