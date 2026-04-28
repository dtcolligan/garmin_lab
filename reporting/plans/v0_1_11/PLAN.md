# v0.1.11 — Audit-cycle deferred items + persona expansion + property tests

> **Status.** PLAN.md draft, ready to open. Authored 2026-04-27 by
> Claude as part of post-v0.1.10 strategic + tactical planning.
> Maintainer reviews, approves, and opens the cycle.
>
> **Source.** Tactical plan §2 (companion). Pulls deferred items
> from v0.1.10 + v0.1.9 backlog + targeted new infrastructure work.
>
> **Cycle pattern.** v0.1.11 follows the four-round audit/response
> convention (Phase 0 pre-PLAN bug hunt, this PLAN.md, Codex audit
> round 1, response + implementation rounds, ship proof).

---

## 1. What this release ships

v0.1.11 closes every workstream v0.1.10 deferred, expands the
persona matrix from 8 → 12, and introduces property-based testing
for the policy DSL. End-state: every named finding from
`v0_1_10/audit_findings.md` is either fixed or formally deferred to
v0.2+.

### 1.1 Workstream catalogue

| W-id | Title | Severity | Files (primary) | Source |
|---|---|---|---|---|
| **W-B** | R-volume-spike minimum-coverage gate | band-miscalibration | `core/synthesis_policy.py`, `domains/strength/policy.py`, `core/config.py` | F-C-04, B2 (memory) |
| **W-E** | `hai daily` re-run state-change supersession | audit-chain-break | `core/synthesis.py`, `cli.py` daily handler | F-B-02, B7 (memory) |
| **W-F** | Audit-chain version-counter integrity | audit-chain-break | `core/synthesis.py` supersession path | F-B-01 |
| **W-H1** | Mypy correctness-class fixes | correctness | `cli.py`, `core/synthesis.py`, `evals/runner.py`, `core/state/runtime_event_log.py`, `core/state/projector.py`, `core/doctor/checks.py` | F-A-03, F-A-04, F-A-05, F-A-06, F-A-07, F-A-11 |
| **W-K** | Bandit B608 site-by-site verdict | security review | 8 files (16 sites) | F-A-13 |
| **W-L** | Bandit B310 url-scheme audit | security | `core/pull/intervals_icu.py:310` | F-A-14 |
| **W-N** | Pytest unraisable warning cleanup | nit | `safety/tests/test_snapshot_bundle.py` | v0.1.9 backlog |
| **W-O** | Persona matrix expansion (8 → 12) | infrastructure | `verification/dogfood/personas/p9-p12_*.py` | NEW |
| **W-P** | Property-based tests for policy DSL | testing infrastructure | `verification/tests/test_policy_dsl_invariants.py` | NEW |
| **W-Q** | F-B-03 review-schedule auto-run investigation | audit-chain integrity (investigative) | `cli.py` daily handler, `core/review/outcomes.py` | F-B-03 |
| **W-R** | F-C-03 / F-CDX-IR-05 — running-rollup provenance + completeness | correctness polish | `cli.py` clean handler, `core/state/projector.py` | v0.1.10 W-D-ext follow-up + Codex round 1 |
| **W-S** | F-CDX-IR-06 — persona harness drift guards | testing infrastructure | `verification/dogfood/synthetic_skill.py`, new contract test | Codex round 1 |
| **W-T** | F-CDX-IR-R3-N1 — in-memory threshold injection seam audit | trusted-seam audit | `core/config.py`, every `evaluate_*` / classify / policy entry point | Codex round 3 |

### 1.2 Out-of-scope (deferred)

| Item | Why deferred |
|---|---|
| **W-H2** mypy stylistic fixes (Literal abuse, redefinition, scenario type confusion) | v0.1.12 scope per tactical plan — different class than W-H1 correctness |
| **F-B-04** domain-coverage drift across supersession | Semantic question, needs design discussion; v0.1.12 W-U |
| **F-C-05** strength_status enum surfaceability | Capabilities-manifest extension; v0.1.12 W-V |
| **F-C-06** persona matrix elevated-stress coverage | Rolled into W-O (persona expansion includes elevated-stress P11) |
| **W52 / W53 / W58** | v0.2.0 wave per strategic plan |

---

## 2. Per-workstream contract

### 2.1 W-B — R-volume-spike minimum-coverage gate

**Goal.** Stop R-volume-spike escalating for users with regular but
sparse strength training. Confirmed across 6 personas in v0.1.10.

**Approach.**
- Add `min_sessions_last_28d` threshold to the rule. Default `8`
  (≥2 sessions/week sustained).
- Below threshold → rule emits `coverage_band: 'insufficient'`
  rather than firing as spike.
- Rule firing path checks gate first; classification stays as-is.

**Files:**
- `src/health_agent_infra/core/synthesis_policy.py` — X-rule body.
- `src/health_agent_infra/domains/strength/policy.py` — R-rule body
  if it shares the trigger.
- `src/health_agent_infra/core/config.py` — DEFAULT_THRESHOLDS new
  entry.

**Tests:**
- `verification/tests/test_xrule_volume_spike_coverage.py` (new) —
  boundary tests around `min_sessions_last_28d`.
- Persona matrix re-run shows P1, P4, P5, P6, P7 stop escalating
  on regular training pattern (current 6 personas escalate; target
  ≤ 1).

**Acceptance:**
- Persona harness findings drop from 3 → ≤ 1.
- New unit tests cover boundary at 7, 8, 9 sessions.
- DEFAULT_THRESHOLDS gains `r_volume_spike_min_sessions_last_28d`
  with documented rationale.

### 2.2 W-E — `hai daily` re-run state-change supersession

**Goal.** When `hai daily` is re-run on the same date and state
materially differs, produce a superseded `_v<N>` plan with refreshed
rationale prose.

**Approach.**
- `core/synthesis.py` computes a state fingerprint (hash of
  nutrition_intake, readiness, gym intake, clean-evidence row,
  manual readiness/stress) before synthesis.
- If a canonical plan already exists for `(for_date, user_id)`,
  compare its captured fingerprint to current.
- Match → no-op (correct idempotent behaviour).
- Mismatch → produce `_v<N>` supersession with fresh proposal_log
  rows + regenerated rationale prose.

**Schema:** add `state_fingerprint` column to `daily_plan` table
(nullable, populated from v0.1.11 forward; backfilled to NULL for
existing rows). Add migration `NNN_daily_plan_state_fingerprint.sql`.

**Files:**
- `core/synthesis.py` — fingerprint computation + comparison.
- `cli.py` — daily handler invocation surface.
- `core/state/migrations/NNN_*.sql` — new migration.
- `core/schemas.py` — DailyPlan dataclass field.

**Tests:**
- `verification/tests/test_daily_supersede_on_state_change.py`
  (new) — reproduces v0.1.10 morning-briefing scenario.
- Migration round-trip test.

**Acceptance:**
- Reproduce: log nutrition A → daily → log nutrition B (replace) →
  daily again → observe `_v2` plan id with fresh prose.
- Idempotent re-run with no state change is a true no-op (no new
  plan_id, no new proposal_log rows).

### 2.3 W-F — Audit-chain version-counter integrity

**Goal.** Eliminate `_v3` jumps from `_v0` (skipped `_v2`) observed
in F-B-01.

**Approach.**
1. Investigate root cause first. Hypothesis: counter increments on
   attempt, not on commit.
2. Audit `core/synthesis.py` supersession path.
3. Fix: counter increments only after successful commit of the
   superseding row.
4. Regression test: contrived re-synthesise loop with rollback in
   the middle MUST NOT advance the version counter.

**Files:**
- `core/synthesis.py` supersession version-increment path.

**Tests:**
- `verification/tests/test_supersede_version_counter.py` (new) —
  sequential version assertion + rollback-isolation assertion.

**Acceptance:**
- No skipped versions in any chain post-fix.
- Audit-chain probe (manual `hai explain --plan-version all` walk)
  passes for every recent date.

### 2.4 W-H1 — Mypy correctness-class fixes

**Goal.** Address the six mypy errors flagged correctness in
`v0_1_10/audit_findings.md` Phase A.

**Per-finding:**
- **F-A-03** `cli.py:204, 4389` adapter type confusion → fix the
  assignment type using a Protocol or union.
- **F-A-04** `synthesis.py:373` `dict|None` assigned to non-None
  typed var → narrow the type or guard None.
- **F-A-05** `evals/runner.py:668-669` scenario type confusion →
  fix the type annotations OR fix the runtime path if mis-typed.
- **F-A-06** `cli.py:4075, 4083` None-comparison operators → guard.
- **F-A-07** `cli.py:2957-2963` exercise None-into-required-str →
  argparse-required validation OR explicit None guard.
- **F-A-11** `core/state/runtime_event_log.py:54` int-of-Optional
  pattern (4 sites total: state/projector.py:302, 2219;
  doctor/checks.py:276) → guard.

**Tests:** existing tests stay green; add boundary tests for any
None path that wasn't previously exercised.

**Acceptance:**
- mypy default pass: 0 correctness-class errors.
- Stylistic-class errors (~10 remaining) deferred to v0.1.12 W-H2.

### 2.5 W-K — Bandit B608 site-by-site verdict

**Goal.** Per-site determination on each of 16 SQL string-construction
findings from `v0_1_10/audit_findings.md` F-A-13.

**Approach.** For each site:
1. Read the call site.
2. Verify the dynamic part is column-whitelisted from a constant tuple
   (the placeholder-templating IN-clause pattern is safe).
3. Add `# nosec B608  # reason: <specific>` comment.
4. If a site is genuinely unsafe, refactor.

**Files (16 sites):**
```
core/explain/queries.py:452, 572, 585
core/intent/store.py:239, 402
core/memory/store.py:208
core/state/projector.py:390, 617
core/state/projectors/running_activity.py:151, 162
core/state/snapshot.py:97, 348, 352
core/target/store.py:219, 360
evals/runner.py:514
```

**Acceptance:** bandit -ll on `src/`: 0 unsuppressed B608.

### 2.6 W-L — Bandit B310 url-scheme audit

**Goal.** Confirm `core/pull/intervals_icu.py:310` URL is fully
constant + does not accept user input.

**Approach.** Read the call site. If safe, document with
`# nosec B310 # reason: <specific>`. If user input contributes,
restrict via `urllib.parse.urlparse` allowed-schemes check.

**Acceptance:** bandit -ll on `src/`: 0 unsuppressed of any kind.

### 2.7 W-N — Pytest unraisable warning cleanup

**Goal.** Eliminate `PytestUnraisableExceptionWarning` from
`safety/tests/test_snapshot_bundle.py::test_snapshot_v1_0_recovery_block_has_three_keys`.

**Approach.** Audit the test for HTTP-client lifecycle (likely an
unclosed response in an intervals.icu auth-check or similar).
Ensure response is closed in a `finally` block or `with` context.

**Acceptance:** `uv run pytest verification/tests safety/tests -W error::Warning` passes clean.

### 2.8 W-O — Persona matrix expansion (8 → 12)

**Goal.** Add four personas to fill matrix gaps.

**New personas:**

| ID | Persona | Why |
|---|---|---|
| **P9** | Older female endurance (52F, 60kg, 165cm, masters runner, 12mo Garmin history) | Female + age-50+ + endurance — none of the above in current matrix |
| **P10** | Adolescent recreational (17M, 65kg, 170cm, casual sport, 6mo) | Below-spec age band. Tests graceful failure or out-of-supported-set surface. |
| **P11** | Elevated-stress hybrid (28M, 78kg, 178cm, persistent elevated stress + body-battery low) | F-C-06 — current matrix is uniform low-stress. Need persona stressing the stress domain. |
| **P12** | Vacation-returner (35F, 65kg, 168cm, 14d gap then back to baseline) | Comeback-from-gap edge. Tests classifier behaviour after data discontinuity. |

**Files:**
- `verification/dogfood/personas/p9_older_female_endurance.py`
- `verification/dogfood/personas/p10_adolescent_recreational.py`
- `verification/dogfood/personas/p11_elevated_stress_hybrid.py`
- `verification/dogfood/personas/p12_vacation_returner.py`
- `verification/dogfood/personas/__init__.py` updated `ALL_PERSONAS`.

**Acceptance:**
- All 12 personas run cleanly through the harness.
- P10's expected behaviour explicitly documented (likely defer
  everything OR explicit "out of supported user set" surface).
- P11 surfaces stress-domain `elevated` band → stress action
  `schedule_decompression_time` or equivalent.

### 2.9 W-P — Property-based tests for policy DSL

**Goal.** Hypothesis-based tests asserting policy-DSL invariants
across ranges of inputs.

**Invariants:**
- For all classified_state inputs in valid ranges,
  `evaluate_<domain>_policy` returns a result whose
  `forced_action` (if not None) is in the domain's action enum.
- For all proposal inputs, `apply_phase_a` returns `mutated` with
  `action` in the domain's action enum.
- For all snapshots, X-rule `recommended_mutation.action` (when
  present) is in the target domain's enum.

**Files:**
- `verification/tests/test_policy_dsl_invariants.py` (new).

**Acceptance:**
- Hypothesis-based tests pass on all 6 domains' policy entry points.
- Any failing case = fix-now scope (likely surfaces a real bug or a
  miscoded enum).

### 2.10 W-Q — F-B-03 review-schedule auto-run investigation

**Goal.** Determine whether 2026-04-25 + 2026-04-26 missing reviews
is regression, intended-manual, or bug.

**Approach.** Read `cli.py` daily handler review-schedule path.
Read `core/review/outcomes.py` schedule entry. Trace whether
`hai daily` auto-schedules reviews unconditionally, or only when
flags align.

**Acceptance:**
- Verdict documented in cycle response.
- If regression: fix + regression test.
- If intended-manual: doc update + UX surface (`hai today` mentions
  review schedule status).

### 2.11 W-R — F-C-03 / F-CDX-IR-05 — running-rollup provenance + completeness

**Goal.** Decide whether `aggregate_activities_to_daily_rollup`
output's `session_count` and `total_duration_s` should populate
`accepted_running_state_daily` (currently hardcoded None per v1
contract per `state_model_v1.md §8`); fix the `derivation_path`
provenance string to distinguish activity-rollup origins from
true `garmin_daily` origins.

**Approach.**
1. Read `state_model_v1.md §8` to understand original intent.
2. Decide: extend v1 contract (populate these fields) OR keep
   intentional NULL.
3. If populating: update projector + tests.
4. If keeping NULL: document the reason explicitly + update
   `state_model_v1.md`.
5. Fix `derivation_path` so rows derived via
   `aggregate_activities_to_daily_rollup` stamp a distinct enum
   value (e.g. `activity_rollup`); rows pulled directly from
   `/wellness.json` keep `garmin_daily` (or `intervals_icu_wellness`).

**Acceptance:**
- Explicit decision documented; if populating, test coverage for
  both fields.
- A new `verification/tests/test_running_provenance.py` asserts
  that personas P2 and P7 (with logged activities) produce rows
  whose `derivation_path` reflects the rollup origin.

### 2.12 W-S — F-CDX-IR-06 persona harness drift guards

**Goal.** Replace hardcoded action-token + schema-version
mappings in `verification/dogfood/synthetic_skill.py` with imports
from the runtime contract, and add a contract test that catches
drift directly rather than via downstream `hai propose` failure.

**Approach.**
1. Replace `_DOMAIN_DEFAULT_ACTION` and `_STATUS_TO_ACTION`
   constants with values pulled from
   `core/validate.ALLOWED_ACTIONS_BY_DOMAIN` plus the proposal
   schema registry.
2. Replace `f"{domain}_proposal.v1"` with the actual schema-version
   constant from the validator module.
3. Add `verification/tests/test_persona_harness_contract.py`
   asserting:
   - Every domain in `ALLOWED_ACTIONS_BY_DOMAIN` appears in the
     harness's status mapping.
   - Every status the harness emits is a valid action for its
     domain.
   - The schema versions match the runtime registry.

**Acceptance:**
- Harness no longer hardcodes runtime contract values.
- Contract test catches a deliberate mutation in either direction
  (proposal schema version bump, action token rename).
- Persona harness re-run produces the same matrix as v0.1.10.

### 2.13 W-T — F-CDX-IR-R3-N1 in-memory threshold injection audit

**Goal.** Resolve the trusted-seam concern Codex round 3 raised
(`SHIP_WITH_NOTES` note 1). `load_thresholds()` validates the
user-TOML boundary, but every `evaluate_*` / classify / policy
entry point accepts a `thresholds: Optional[dict]` argument that
bypasses `_validate_threshold_types` when a caller constructs the
dict in-memory.

**Approach.**

1. Audit every call site that passes a non-`None` `thresholds`
   argument. Categorise: production flow (transitively
   validated), test (trusted by design), other.
2. If only production + test callers exist (the likely outcome),
   document the seam explicitly in:
   - `core/config.py` module docstring.
   - The docstring of every `evaluate_*` / classify / policy
     entry point that accepts the arg.
   - `AGENTS.md` "Settled Decisions" as D13 so the trust
     boundary is load-bearing knowledge.
3. If a non-test, non-production-flow caller exists, choose:
   - Extend `_validate_threshold_types` to support partial
     defaults so it can run at every internal entry point; OR
   - Wrap each entry point with a load-or-pass-through helper.

**Acceptance:**
- Audit summary in `v0_1_11/W_T_audit.md` enumerates every call
  site + its category.
- If documentation-only outcome: AGENTS.md D13 added; module +
  function docstrings updated.
- If extended-validation outcome: validator handles partial
  defaults; new tests cover bool-on-numeric rejection through
  every entry point.
- No regression in existing 2202 + new tests.

---

## 3. Acceptance criteria (ship gates)

v0.1.11 ships when:

- [ ] All 14 workstreams (W-B, W-E, W-F, W-H1, W-K, W-L, W-N, W-O,
      W-P, W-Q, W-R, W-S, W-T, plus the v0.1.10 round-2 / round-3
      carry-overs if any reopen) complete OR explicitly deferred
      with documented reason.
- [ ] **W-E and W-F are tagged release-blocker-class.** v0.1.11 cannot
      ship without both — they are the audit-chain-integrity thesis
      of the release per the v0.1.10 rescope decision.
- [ ] `verification/tests/` green: ≥ 2200 tests passing (was 2169
      at v0.1.10 ship; +30+ from new tests).
- [ ] Persona harness re-runs show:
  - W-B: persona matrix findings drop from 3 → ≤ 1.
  - All 12 personas run without crashes.
- [ ] mypy correctness-class errors: 0 (stylistic-class deferred).
- [ ] ruff strict pass: 0 findings.
- [ ] bandit -ll: 0 unsuppressed findings.
- [ ] `hai capabilities --json` regenerates without diff against
      manifest schema.
- [ ] `verification/tests` runs with `-W error::Warning` clean.
- [ ] CHANGELOG.md updated with v0.1.11 section + per-W-id summary.
- [ ] `RELEASE_PROOF.md` emitted with full pytest log + persona
      harness re-run output.
- [ ] Codex audit round 1 returns SHIP or SHIP_WITH_NOTES.

---

## 4. Sequencing (recommended)

1. **W-N** (pytest warning) — 30 min, smoke-clearer.
2. **W-L** (bandit B310) — 30 min, single-site review.
3. **W-K** (bandit B608) — half-day, all 16 sites in one pass.
4. **W-Q** (review-schedule investigation) — 1-2 days, may inform
   W-E decisions.
5. **W-B** (volume_spike gate) — 1-2 days. Independent.
6. **W-O** (persona expansion) — 2-3 days. Parallel with W-B.
7. **W-P** (property tests) — 2-3 days. May surface bugs that
   reshape later workstreams.
8. **W-H1** (mypy correctness) — 2-3 days. Picks up incidental
   fixes from earlier work.
9. **W-R** (rollup edge cases) — 1 day. Decision + test.
10. **W-E** (state-change supersession) — 2-3 days. Schema
    migration + synthesis path; do this when other workstreams
    are stable.
11. **W-F** (version counter) — 1-2 days. Builds on W-E
    investigation.
12. Persona harness re-run → confirm fixes visible.
13. Codex round 1 audit.

Total: 15-20 days. Realistic ship: 4-5 calendar weeks from open.

---

## 5. Risk register (cycle-specific)

- **W-E schema migration** is the highest-risk item. Touches the
  daily_plan table. Migration round-trip test is a hard gate.
- **W-P property tests** may surface bugs that bloat scope. If
  hypothesis finds something the deterministic tests missed,
  triage it: fix-now if correctness, defer to v0.1.12 if
  edge-case stylistic.
- **W-O P10 (adolescent)** is deliberately out-of-supported-set.
  The test isn't "P10 produces good recommendations" — it's "P10
  fails gracefully." Expected output language matters; cycle
  must align on what "out of supported set" looks like at the CLI
  surface.
- **W-K bandit verdicts** may reveal a genuine SQL-injection vector
  (very unlikely given the patterns surveyed in v0.1.10, but the
  pass exists to prove it). If so, it becomes the highest-priority
  fix and reshapes the cycle.

---

## 6. Provenance

This PLAN.md is built on:

- `reporting/plans/strategic_plan_v1.md` § 7 Wave 1.
- `reporting/plans/tactical_plan_v0_1_x.md` § 2.
- `reporting/plans/v0_1_10/audit_findings.md` (deferred items).
- `reporting/plans/v0_1_10/RELEASE_PROOF.md` (test surface baseline).
- `reporting/plans/v0_1_9/BACKLOG.md` (W-N carry-over).

Out-of-scope items (§ 1.2) carry their deferred-because reasons
forward into the v0.1.11 BACKLOG.md after this cycle ships.
