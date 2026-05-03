# Nutrition Domain

Nutrition is macros-only in v1. It evaluates calories, protein, hydration, and
target availability without pretending to understand micronutrients or food
taxonomy.

## Runtime surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/nutrition/schemas.py` |
| Classifier | `src/health_agent_infra/domains/nutrition/classify.py` |
| Policy | `src/health_agent_infra/domains/nutrition/policy.py` |
| Signals | `src/health_agent_infra/domains/nutrition/signals.py` |
| Intake | `src/health_agent_infra/domains/nutrition/intake.py` |
| Skill | `src/health_agent_infra/skills/nutrition-alignment/SKILL.md` |

## Inputs and accepted state

Nutrition reads daily macro intake rows and nutrition target rows. `hai intake
nutrition` records daily macros; `hai target nutrition` writes the four macro
targets (`calories_kcal`, `protein_g`, `carbs_g`, `fat_g`) over the existing
`target` table.

## Classifier output

`ClassifiedNutritionState` emits:

- `calorie_balance_band`
- `protein_sufficiency_band`
- `hydration_band`
- `micronutrient_coverage`
- `coverage_band`
- `nutrition_status`
- `nutrition_score`
- `goal_alignment_note`
- `uncertainty`

Partial-day/no-target cases short-circuit to
`nutrition_status='insufficient_data'` so breakfast-only intake is not judged
against a full-day target.

## Policy rules

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when macro evidence is insufficient. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse coverage. |
| `extreme_deficiency_escalation` | Forces `escalate_for_user_review` when calorie deficit and protein ratio are both extreme after enough meals. |

## Action enum

- `maintain_targets`
- `increase_protein_intake`
- `increase_hydration`
- `reduce_calorie_deficit`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## Cross-domain participation

Nutrition underfuelling can soften hard recovery/strength/running proposals
through X2. Hard training-domain drafts can cause X9 to append a protein-target
adjustment to a nutrition recommendation's `action_detail` without changing the
nutrition action.

## Skill contract

The nutrition skill uses the W-A presence block, target status, classifier
bands, and policy result to choose recap-vs-forward-march framing. It must not
invent missing targets, infer micronutrients, or classify partial-day intake as
a complete-day failure.
