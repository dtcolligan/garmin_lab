# Contributing

Thanks for taking a look at Health Agent Infra (internal codename: Health Lab).

## Canonical organizing rule

Please review and change this repo through the canonical eight-bucket model:

- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

These are the only canonical project-shape categories. Implementation namespaces inside them, like `clean/health_model/`, are real current paths but not separate canonical layers.

## Current contribution shape

This repo is currently easiest to review as a bounded proof repo with one CLI-first flagship path, supporting proof artifacts, and compatibility surfaces.

Start here:
- `README.md`
- `STATUS.md`
- `reporting/docs/canonical_doctrine.md`
- `reporting/docs/flagship_loop_spec.md`
- `reporting/docs/flagship_walkthrough.md`
- `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/` — current flagship synthetic proof
- `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` — current flagship real Garmin slice
- `reporting/docs/v1_source_scope.md`
- `reporting/docs/source_registry_v1.md`
- `reporting/docs/source_adapter_contract_v1.md`

For current source-scope and connector-truth review, preserve this doctrine:
- manual structured gym logs are the current source-of-truth path
- `wger` remains bounded exploratory non-flagship only
- the next bounded deliverable is Phase 3 connector-truth/source-registry reconciliation
- manual `program_block` is not the current next slice

## Contribution boundaries

Please keep contributions truthful to current repo reality:
- do not introduce new canonical project categories outside the eight buckets
- do not present `health_model` as a canonical repo layer rather than an implementation namespace inside `clean`
- do not overclaim clinical, diagnostic, or production readiness
- do not treat local runtime data as public-safe demo material unless it is explicitly curated under reporting proof surfaces
- prefer small changes that preserve fail-closed behavior, proof integrity, and honest docs
- keep destructive moves, deletes, or package redesign out of scope unless explicitly approved

## Before opening a PR

1. Check that your change fits one of the eight canonical buckets.
2. Keep README, STATUS, and reporting docs aligned with actual repo paths and proofs.
3. If you touch source-scope or connector-truth docs, keep the three Phase 3 source-truth docs above aligned with the root review surfaces.
4. If you touch the flagship loop, run the relevant bounded tests.
5. If you change proof-facing docs or artifacts, make sure links resolve from repo root and claims stay narrower than the checked-in evidence.

Current flagship smoke test command:

```bash
PYTHONPATH=clean:safety uv run --with pytest pytest safety/tests/test_recovery_readiness_v1.py -v
```

## Good first changes

- bucket-model documentation cleanup
- bounded CLI reliability improvements
- tighter proof artifacts and audit notes
- tests that strengthen the existing flagship loop
- truthful path corrections where old `data/...` teaching no longer matches repo reality

Large renames, product reframes, hosted-service work, UI expansion, archive cleanup, or broader namespace redesign should be discussed before implementation.
