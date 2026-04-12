# Health Lab

Health Lab is a bucket-organized infrastructure repo for agent-mediated personal health work over user-owned memory.

The canonical project shape is only these eight buckets:

- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

Anything else in the repo should be treated as implementation detail, compatibility surface, proof material, or legacy/archive content, not as an extra canonical layer.

## Repo truth right now

This repo currently exposes a narrow CLI-first proof path plus supporting docs, tests, and artifacts. It is not a hosted product, polished consumer app, clinical system, or the durable private memory authority for user health data.

Current implementation locations that matter for review:

- `pull/` contains passive and machine-readable input acquisition surfaces and current local runtime data locations such as `pull/data/garmin/` and `pull/data/health/`
- `clean/health_model/` contains the main current deterministic cleaning and contract-oriented implementation namespace
- `merge_human_inputs/` contains current human-input intake and manual logging surfaces
- `reporting/` contains operator-facing docs, scripts, and checked-in proof artifacts
- `writeback/agent_memory_write_cli.py` is the current explicit writeback entrypoint
- `safety/` contains tests, compatibility wrappers, and safety-oriented proof enforcement surfaces
- `research/` and `interpretation/` hold exploratory or model-oriented work within their respective buckets
- `archive/legacy_product_surfaces/` contains older adjacent surfaces and is not part of the canonical current review path

Important rule: namespaces inside a bucket, like `clean/health_model/`, are current implementation locations within that bucket. They are not separate canonical project-shape categories.

## Bucket model

### `pull`
Deterministic acquisition of passive or machine-readable inputs.

### `clean`
Deterministic normalization, validation, bundle assembly, retrieval shaping, and preparation of interpretation-ready artifacts.

### `merge_human_inputs`
Human notes, voice-note intake, manual logs, and related merge surfaces that sit between deterministic infra and later interpretation.

### `research`
Exploration, notebooks, and bounded research material.

### `interpretation`
Model-oriented interpretation code and experiments. This bucket is distinct from the deterministic infra buckets.

### `reporting`
Docs, proof bundles, review artifacts, and operator-facing runnable demos.

### `writeback`
Explicit persisted state or memory update surfaces.

### `safety`
Compatibility wrappers, tests, fail-closed checks, and trust-boundary enforcement.

## Current flagship proof path

The clearest public proof is still the CLI-first loop:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

Today that loop is implemented mainly from `clean/health_model/`, with compatibility wrappers also present under `safety/health_agent_infra/` and the writeback surface exposed under `writeback/`.

Start with:

- `reporting/docs/health_lab_canonical_definition.md`
- `reporting/docs/health_lab_canonical_public_demo.md`
- `reporting/artifacts/public_demo/captured/`
- `reporting/artifacts/flagship_loop_proof/2026-04-09/`
- `STATUS.md`

Run the canonical public demo from repo root:

```bash
python3 reporting/scripts/run_canonical_public_demo.py
```

## Current path truth

Older docs often taught runtime outputs under top-level `data/`. Current repo truth is more mixed:

- checked-in public proof artifacts live under `reporting/artifacts/`
- many disposable demo/runtime examples still write under `data/` paths in command examples
- current repo-local runtime data also exists under bucketed locations such as `pull/data/`

When updating docs or commands, prefer the real path used by the specific script or CLI, and do not teach `data/...` as a universal canonical repo root.

## What is proven now

- contract discovery via `PYTHONPATH=clean:safety python3 -m health_model.agent_contract_cli describe`
- bundle initialization via `PYTHONPATH=clean:safety python3 -m health_model.agent_bundle_cli init`
- same-day voice-note submission via `PYTHONPATH=clean:safety python3 -m health_model.agent_voice_note_cli submit`
- scoped context reads via `PYTHONPATH=clean:safety python3 -m health_model.agent_context_cli get`
- recommendation creation via `PYTHONPATH=clean:safety python3 -m health_model.agent_recommendation_cli create`
- bounded recommendation-judgment writeback via `PYTHONPATH=clean:safety python3 -m health_model.agent_memory_write_cli recommendation-judgment`

## Not claimed

- not a clinical product or medical device
- not a hosted multi-user product
- not a polished general-user install flow
- not a claim that `health_model` is a canonical project layer
- not a claim that every repo surface has already been reorganized around the bucket model

## Contributing and review

For truthful review and contribution guidance, see:

- `STATUS.md`
- `CONTRIBUTING.md`
- `reporting/docs/offline_garmin_export_adapter.md`
- `reporting/docs/health_lab_canonical_definition.md`
