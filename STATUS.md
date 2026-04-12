# Status

## Canonical repo framing

This repo should be read through the canonical eight-bucket model only:

- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

Those eight buckets are the only canonical project-shape categories. Subpaths inside them, such as `clean/health_model/` or `writeback/agent_memory_write_cli.py`, are current implementation locations, not separate canonical layers.

## Current repo reality

The repo currently presents one bounded, CLI-first proof path plus supporting artifacts, tests, and compatibility surfaces. It is not a hosted product, consumer app, clinical system, or the durable private memory authority for user health data.

Current implementation highlights by bucket:

- `pull/` contains passive-data and machine-readable input acquisition surfaces plus current bucket-local runtime data paths such as `pull/data/`
- `clean/health_model/` is the current main deterministic implementation namespace inside the `clean` bucket
- `merge_human_inputs/` contains manual logging and intake surfaces
- `reporting/` contains docs, scripts, public demo material, and proof bundles
- `writeback/` contains explicit persisted-update surfaces
- `safety/` contains tests, fail-closed proof checks, and compatibility wrappers
- `research/` and `interpretation/` contain bounded exploratory and model-oriented work in their own buckets
- `archive/legacy_product_surfaces/` remains legacy material outside the canonical bucket model

## Proven now

The clearest current proof loop is:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

That proof is currently taught through bucketed implementation paths, mainly `clean/health_model/`, with temporary compatibility wrappers under `safety/health_agent_infra/`.

Public review surfaces:

- `reporting/docs/health_lab_canonical_definition.md`
- `reporting/docs/health_lab_canonical_public_demo.md`
- `reporting/artifacts/public_demo/captured/`
- `reporting/artifacts/flagship_loop_proof/2026-04-09/`

Additional bounded writeback proof:

- `reporting/artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`
- `reporting/artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/`

## Pathing truth to keep straight

- checked-in proof artifacts live under `reporting/artifacts/`
- some runtime examples still write to `data/` paths
- current bucket-local runtime data also exists under `pull/data/`

So `data/...` should not be taught as the universal canonical repo layout.

## What this repo is not claiming

- not a clinical product or medical device
- not a hosted or multi-user runtime
- not a polished install flow for general users
- not a claim that `health_model` is a canonical project-shape category
- not a claim that all older adjacent material has been deleted or reorganized

## Reviewer checklist

- [x] Root docs now frame the repo through the canonical eight buckets
- [x] Touched public/operator-facing docs demote `health_model` to implementation-namespace status
- [x] Current path teaching avoids treating `data/...` as universal repo truth
- [x] Public proof surfaces remain rooted in `reporting/`
- [x] Legacy material stays explicitly non-canonical
- [ ] Destructive cleanup, moves, and archive pruning remain deferred to later slices
