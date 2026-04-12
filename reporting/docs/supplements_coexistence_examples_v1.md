# supplements coexistence examples v1

This proof bundle freezes the bounded v1 coexistence contract for Cronometer-derived and manual `supplement_intake` records.

## Contract summary

- Cronometer is the preferred machine-readable source for supplements in v1.
- Manual supplements remain valid fallback and backfill inputs.
- V1 does not silently merge or silently override overlap between Cronometer and manual supplement records.
- Overlap must resolve explicitly as `superseded` or `coexists_conflicted`.

## Decision table

| Case | Inputs present | Expected retained behavior | Conflict status expectation |
| --- | --- | --- | --- |
| Cronometer only | Cronometer receipt has supplement detail, no manual counterpart | emit Cronometer-derived `supplement_intake` | `none` |
| Manual only fallback | no trustworthy Cronometer supplement detail for the intake/day, manual artifact exists | emit manual `supplement_intake` | `none` |
| Overlap, deterministic duplicate | Cronometer and manual records match on substance, date, and available time/dose anchors closely enough | retain one primary representation, keep the other provenance path visible as duplicate | duplicate path `superseded` |
| Overlap, ambiguous | Cronometer and manual records share substance/date but timing or dose anchors are missing or inconsistent | keep both visible, do not collapse | `coexists_conflicted` |

## Example A, Cronometer only

Raw source shape:
- source: `cronometer`
- day anchor: `2026-04-11`
- receipt family: export CSV for the day
- intake: magnesium glycinate 200 mg at 21:00

Expected canonical output:

```yaml
supplement_intake:
  source_name: cronometer
  source_record_id: nutrition:cronometer:day:2026-04-11:supplement:magnesium-glycinate:2100:200-mg
  provenance_record_id: provenance:nutrition:cronometer:day:2026-04-11:supplement:magnesium-glycinate:2100:200-mg
  conflict_status: none
  substance_name: Magnesium Glycinate
  dose_value: 200
  dose_unit: mg
  taken_at: 2026-04-11T21:00:00
```

## Example B, manual only fallback

Raw source shape:
- source: manual supplement artifact `telegram-note-2026-04-11-2204`
- no trustworthy Cronometer supplement detail for the intake/day
- intake: vitamin D3 1000 IU at 22:04

Expected canonical output:

```yaml
supplement_intake:
  source_name: supplements
  source_record_id: supplement:telegram-note-2026-04-11-2204:2026-04-11T22:04:00:vitamin-d3
  provenance_record_id: provenance:supplement:telegram-note-2026-04-11-2204:2026-04-11T22:04:00:vitamin-d3
  conflict_status: none
  substance_name: Vitamin D3
  dose_value: 1000
  dose_unit: IU
  taken_at: 2026-04-11T22:04:00
```

## Example C, overlap with deterministic duplicate resolution

Input pair:
- Cronometer: omega-3 fish oil 1000 mg on `2026-04-11` at `08:00`
- Manual artifact: same substance on same date at `08:03`, same dose

Resolution rule used:
- substance matches
- effective date matches
- time window is close enough
- dose anchors are compatible

Expected canonical outputs:

```yaml
primary_supplement_intake:
  source_name: cronometer
  source_record_id: nutrition:cronometer:day:2026-04-11:supplement:omega-3-fish-oil:0800:1000-mg
  provenance_record_id: provenance:nutrition:cronometer:day:2026-04-11:supplement:omega-3-fish-oil:0800:1000-mg
  conflict_status: none
  substance_name: Omega-3 Fish Oil
  dose_value: 1000
  dose_unit: mg
  taken_at: 2026-04-11T08:00:00

superseded_duplicate_record:
  source_name: supplements
  source_record_id: supplement:manual-log-2026-04-11:2026-04-11T08:03:00:omega-3-fish-oil
  provenance_record_id: provenance:supplement:manual-log-2026-04-11:2026-04-11T08:03:00:omega-3-fish-oil
  conflict_status: superseded
  substance_name: Omega-3 Fish Oil
  dose_value: 1000
  dose_unit: mg
  taken_at: 2026-04-11T08:03:00
```

## Example D, overlap with unresolved ambiguity

Input pair:
- Cronometer: magnesium glycinate 200 mg on `2026-04-11`, time unavailable
- Manual artifact: magnesium glycinate 350 mg on `2026-04-11` at `21:30`

Why ambiguity remains:
- substance matches
- effective date matches
- time anchor is missing on Cronometer side
- dose anchors differ materially

Expected canonical outputs:

```yaml
cronometer_record:
  source_name: cronometer
  source_record_id: nutrition:cronometer:day:2026-04-11:supplement:magnesium-glycinate:date-only
  provenance_record_id: provenance:nutrition:cronometer:day:2026-04-11:supplement:magnesium-glycinate:date-only
  conflict_status: coexists_conflicted
  substance_name: Magnesium Glycinate
  dose_value: 200
  dose_unit: mg

manual_record:
  source_name: supplements
  source_record_id: supplement:manual-log-2026-04-11:2026-04-11T21:30:00:magnesium-glycinate
  provenance_record_id: provenance:supplement:manual-log-2026-04-11:2026-04-11T21:30:00:magnesium-glycinate
  conflict_status: coexists_conflicted
  substance_name: Magnesium Glycinate
  dose_value: 350
  dose_unit: mg
  taken_at: 2026-04-11T21:30:00
```

## Replay and idempotency note

Repeated processing of the same Cronometer day receipt and the same manual artifact must preserve the same `source_record_id` values above.

Cross-source overlap must not collapse source identities by accident. Only explicit deterministic duplicate resolution may mark one path `superseded`, and that decision must remain inspectable through provenance.

## Non-goal note

This slice does not implement a Cronometer connector or broad supplement ingestion. It only freezes the bounded coexistence contract and proof examples needed before implementation.
