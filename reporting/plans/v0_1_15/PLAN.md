# v0.1.15 PLAN — Foreign-user candidate package + recorded gate

**Status:** D14 closed in-place at round 3 (round-1 PLAN_COHERENT_WITH_REVISIONS, 12 findings; round-2 PLAN_COHERENT_WITH_REVISIONS, 7 findings; round-3 PLAN_COHERENT_WITH_REVISIONS, 3 nit-class findings closed in-place per round-3 prompt Step 4). Phase 0 (D11) bug-hunt opens next.
**Authored:** 2026-05-02 evening; superseded the round-0 draft (over-scoped 16-slot "everything queued" combined cycle).
**Cycle tier (D15):** **substantive** — W-2U-GATE release-blocker + W-C state-model edit (new `nutrition_target` table + migration) + W-GYM-SETID schema-data migration + F-PV14-01 audit-chain edit ≥ 3 governance/state-model/audit-chain edits.
**Estimated effort:** **16-25 days** (1 maintainer). See §5 arithmetic. Range widened from round-1's 14-20 to reflect (a) W-GYM-SETID JSONL-recovery acceptance split and (b) W-2U-GATE coordination overhead.
**D14 expectation:** budget 2-4 rounds per AGENTS.md empirical norm; round-1 surfaced 12 findings (mostly cross-doc consistency + acceptance bite), round-2 should drop to 4-7 if the halving signature holds.

**Theme.** Make the package usable for a non-maintainer on a foreign machine, ship a recorded gate session against that user, and reserve v0.1.16 strictly for empirical bugs the gate surfaces. Maintainability work (W-29 cli.py split, eval-substrate W-AH-2/W-AI-2/W-AM-2/W-Vb-4) and nice-to-haves (W-B intake weight, W-D arm-2 projection, F-PV14-02 surgical-cleanup CLI) are deferred to **v0.1.17** ("maintainability + eval consolidation"). See §1.4 scope-decision provenance.

**Source inputs:**
- `post_v0_1_14/agent_state_visibility_findings.md` — F-AV-01..05 (W-A through W-E originally proposed for v0.1.16).
- `post_v0_1_14/carry_over_findings.md` — F-PV14-01 (CSV-fixture isolation; F-PV14-02 deferred to v0.1.17).
- `v0_1_14/RELEASE_PROOF.md` §carry-overs — W-2U-GATE inherited; W-29 / W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4 deferred to v0.1.17.
- `tactical_plan_v0_1_x.md` rows 46-48 (post-restructure: v0.1.15 / v0.1.16 / v0.1.17).
- 2026-05-02 evening user-facing session that surfaced **W-GYM-SETID** (gym-set PK collision; not previously catalogued).

---

## 1. What this release ships

### 1.1 Theme

A foreign user installs the package on a fresh device, runs morning ritual + intake + `hai today` end-to-end, talks to their host agent, and reaches `synthesized` without hitting the agent-state-visibility class of bugs. The recorded session is the ship claim.

### 1.2 Workstream catalogue (7 W-ids)

| Section | W-id | Title | Effort | Tier | Source |
|---|---|---|---|---|---|
| §2.A | **W-GYM-SETID** | Gym set-id PK collision fix (multi-exercise sessions) + prospective SQL migration + required fixture | 1.5-3 d | NEW | this PLAN §2.A; repro evidence in user state |
| §2.B | **W-A** | `hai intake gaps` extended with `present` block + `is_partial_day` signal + `target_status` enum | 2-3 d | pulled from v0.1.16 | `agent_state_visibility_findings.md` F-AV-01 |
| §2.C | **F-PV14-01** | CSV-fixture pull isolation marker (default-deny without `hai demo` or explicit override) | 1-2 d | carry-over | `post_v0_1_14/carry_over_findings.md` F-PV14-01 |
| §2.D | **W-C** | `hai target nutrition` daily macro target commit (W57-gated) + `nutrition_target` table + migration | 3-4 d | pulled from v0.1.16 | `agent_state_visibility_findings.md` F-AV-03 |
| §2.E | **W-D arm-1** | Suppress nutrition classification when partial-day + no target (`status=insufficient_data`, reason `partial_day_no_target`) | 1-2 d | pulled from v0.1.16, partial | `agent_state_visibility_findings.md` F-AV-04 arm 1 |
| §2.F | **W-E** | `merge-human-inputs` skill update consuming W-A presence tokens; optional packaged `morning-ritual` skill | 2-4 d | pulled from v0.1.16 | `agent_state_visibility_findings.md` F-AV-05 |
| §2.G | **W-2U-GATE** | First non-maintainer foreign-machine recorded session + P0 inline + P1 close-if-cheap | 4-7 d | inherited | v0.1.14 RELEASE_PROOF §carry-overs + tactical row 46 |

**Total:** 7 W-ids, **16-25 days estimated effort** (after §5 coordination overhead; per-WS arithmetic 14.5-19-25), substantive tier. D14 expectation: 2-4 rounds.

### 1.3 Sequencing (DAG, parallelizable Phase 1)

**Phase 1 — Independent runtime fixes (parallelizable):**
1. **W-GYM-SETID** — small, isolated to gym-intake path; migration test.
2. **W-A** — pure read-side extension to `hai intake gaps`; foundation for W-D arm-1 + W-E.
3. **F-PV14-01** — CSV adapter isolation marker; no other WS depends on it.
4. **W-C** — new `nutrition_target` table + W57-gated `hai target nutrition` command.

**Phase 2 — Dependent runtime + skill (after W-A):**
5. **W-D arm-1** — consumes W-A `is_partial_day` signal; suppresses nutrition classification when partial-day + no-target.
6. **W-E** — `merge-human-inputs` skill consumes W-A presence tokens; optional `morning-ritual` skill orchestrates the four-step cycle.

**Phase 3 — Foreign-user gate (ship claim):**
7. **W-2U-GATE** — recorded session against the candidate package built from Phases 1-2. Maintainer-substitute reader runs through morning ritual + intake + `hai today` + agent conversation. P0 (blocks `synthesized`) closed inline; P1 (blocks user-trust) closed inline if cheap, else named-deferred to v0.1.16. P2+ defer to v0.1.16 unconditionally.

### 1.4 Scope-decision provenance

The 2026-05-02 evening saw two scoping rounds, then a 2026-05-03 round-1 audit revision pass:

- **Round 0 (rejected).** Original maintainer override: graft v0.1.16's W-A-E into v0.1.15 alongside W-29 cli.py split + eval substrate (W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4) + F-PV14-02. **16 catalogued slots** (W-D counted as two — arm-1 and arm-2 — because they ship in different cycles), 39-60 days estimated.
- **Round 0 self-audit → round 1 (this PLAN).** Round 0 conflated two objectives: "close out queued work" vs "second user succeeds on a foreign machine." Per-WS audit against the second-user objective: 9 catalogued slots did not materially affect whether the foreign user reaches `synthesized`. Cut to **7 slots** in v0.1.15; **9 slots** deferred to v0.1.17. Including the cut items would have inflated cycle scope by ~50%, created merge friction between W-29 and W-A-E (the exact risk the findings doc warned of), and delayed the empirical foreign-user signal by ~10 weeks.

**One accounting throughout this PLAN and the cross-doc fan-out:** **16 catalogued slots = 7 kept (v0.1.15) + 9 deferred (v0.1.17).** W-D is counted as two slots (arm-1 in v0.1.15, arm-2 in v0.1.17) because the arms ship separately. If a reader prefers "W-D as one W-id with two arms," that's a parenthetical re-counting; the canonical accounting in this PLAN, the v0.1.17 README, and tactical §5B/§5D is the 16-slot table.

**Round-0 → round-1 disposition table** (preserved here so an auditor can reconcile counts without external context; F-PLAN-04 satisfaction):

| Slot | Round-0 W-id | Round-1 disposition | Destination | Reason |
|---|---|---|---|---|
| 1 | W-29 | cut | v0.1.17 | mechanical refactor; doesn't affect foreign-user flow; merges with W-A-E if combined |
| 2 | W-30 | cut | v0.1.17 | regression test for W-29; follows W-29 |
| 3 | W-GYM-SETID | **kept** | v0.1.15 | breaks any multi-exercise session; will hit foreign user |
| 4 | F-PV14-01 | **kept** | v0.1.15 | defensive; CSV-fixture leak would corrupt foreign-user state |
| 5 | F-PV14-02 | cut | v0.1.17 | surgical-cleanup tool; foreign user won't hit a contamination scenario in first session |
| 6 | W-A | **kept** | v0.1.15 | every agent re-asks user without it |
| 7 | W-B | cut | v0.1.17 | weigh-in nice-to-have; foreign-user agent loop works without it (see F-PLAN-09 disposition in response file) |
| 8 | W-C | **kept** | v0.1.15 | target commit needed for sane nutrition-band classification |
| 9 | W-D arm-1 | **kept** | v0.1.15 | mid-day reads classify wrong without it |
| 10 | W-D arm-2 | cut | v0.1.17 | enhancement over arm-1; arm-1 closes the user-trust bug |
| 11 | W-E | **kept** | v0.1.15 | wraps W-A presence in agent prose |
| 12 | W-AH-2 | cut | v0.1.17 | eval substrate; validates fixtures, not real user |
| 13 | W-AI-2 | cut | v0.1.17 | maintainer tool |
| 14 | W-AM-2 | cut | v0.1.17 | eval substrate |
| 15 | W-Vb-4 | cut | v0.1.17 | internal correctness; persona-runner reads post-W-A schema (sequence after) |
| 16 | W-2U-GATE | **kept** | v0.1.15 | IS the ship claim |

**Reconciliation:** 16 round-0 catalogued slots = 7 kept (v0.1.15) + 9 deferred (v0.1.17). All slots accounted for; no orphans.

The findings doc's original v0.1.15-mechanical / v0.1.16-hardening split was structurally right. This PLAN keeps that structural insight but reassigns the labels: the *user-facing hardening* moves into v0.1.15 (where the gate runs), the *maintainability/eval* moves to v0.1.17. The naming change (v0.1.16 → v0.1.17 for maintainability) is so v0.1.16 stays exclusively reserved for empirical post-gate bug fixes per the maintainer's framing.

---

## 2. Per-workstream contracts

### §2.A W-GYM-SETID — gym set-id PK collision (prospective fix; recovery is operator path)

**Repro.** Multi-exercise gym session in maintainer state today (`leg_back_2026-05-02`): JSONL has 11 sets across 4 exercises (Deadlift / Back Squat / Hamstring Curl / Pull-up); `gym_set` table has 3 (Deadlift only); `accepted_resistance_training_state_daily` row has `exercises: ["Deadlift"]`. Root cause: `deterministic_set_id(session_id, set_number) → set_<sid>_001` collides across exercises with overlapping set numbers; SQL silently drops second-and-later sets via `INSERT OR IGNORE`.

**Files of record:** `src/health_agent_infra/domains/strength/intake.py:96-105`, `src/health_agent_infra/cli.py:cmd_intake_gym`, migration in `src/health_agent_infra/core/state/migrations/`, fixture in `verification/tests/fixtures/multi_exercise_session.jsonl` (NEW — required per F-PLAN-07).

**Fix shape — prospective only.**
```python
def deterministic_set_id(session_id: str, exercise_name_slug: str, set_number: int) -> str:
    return f"set_{session_id}_{exercise_name_slug}_{set_number:03d}"
```
`exercise_name_slug` is `_norm(exercise_name)` from `projectors/strength.py`. CLI handler (`cli.py:cmd_intake_gym`) updated to compute and pass the slug.

**Schema migration scope (per F-PLAN-07).** SQL migration only — regenerate `set_id` PK for rows already in `gym_set`. The migration runner (`core/state/store.py:142-160, 243-299`) executes `.sql` files against the DB; it does NOT read JSONL audit logs. Therefore:
- **In scope:** existing `gym_set` rows get their `set_id` rewritten to the new format; supersession chains preserved by replaying `supersedes_set_id` against the new derivation in-SQL.
- **Out of scope (operator-only recovery path):** rows that exist in `~/.health_agent/gym_sessions.jsonl` but were silently dropped at intake (the maintainer's leg+back session has 8 such rows). These are recoverable only via `hai state reproject --base-dir ~/.health_agent --cascade-synthesis` (`cli.py:3041-3049`). The maintainer runs the reproject manually before the foreign-user gate; not part of the W-GYM-SETID schema migration. Documented in §4.3 as the maintainer's pre-gate recovery procedure.

**Required fixture (per F-PLAN-07).** Author `verification/tests/fixtures/multi_exercise_session.jsonl` (4-exercise leg+back session, 11 sets) explicitly. Do NOT gate the multi-exercise migration test on "if any."

**Acceptance.**
1. New test intakes the multi-exercise fixture; asserts every set lands in `gym_set` with a unique PK; asserts `accepted_resistance_training_state_daily` row reflects all 4 exercises in `exercises[]` and correct `volume_by_muscle_group_json` aggregation.
2. Migration test: existing single-exercise rows in `gym_set` survive the migration with set_ids rewritten and supersession chains intact.
3. Migration test: existing-but-dropped rows in JSONL are NOT recovered by the migration alone (asserts the operator-only recovery path is documented, not silently performed during migration).
4. Reproject test: `hai state reproject --base-dir <fixture-path> --cascade-synthesis` on the multi-exercise JSONL fixture against a post-migration DB recovers all 11 sets to `gym_set`.
5. `hai backup` round-trip test on the post-migration DB (verifies F-PLAN-07's backup-format coverage of `gym_set`; per `core/backup/bundle.py:81-82` the backup includes `state.db` + JSONL logs, but the round-trip should be explicit).

### §2.B W-A — `hai intake gaps` presence block + `is_partial_day` + `target_status`

Inherited from `agent_state_visibility_findings.md` F-AV-01 with the predicate split clarified per F-PLAN-01 (round-1) and the typed-contract fix per F-PLAN-R2-01 (round-2). `is_partial_day` is purely a time/intake signal; the `target_status` locator is a separate three-valued enum. This split is required so W-D arm-1 (suppress) can fire correctly across the no-target / no-table-yet states, and so W-D arm-2 (project, deferred to v0.1.17) can fire on a present target without contradictory predicates.

Pure read-side, no schema change beyond the read-path query against `nutrition_target` (W-C dependency for the `target_status` field — see Phase 1 sequencing in §1.3 for the parallelization note). Capabilities manifest update.

**Output contract (round-2 typed):**
- `is_partial_day: bool` — pure time/intake signal, target-independent.
- `target_status: "present" | "absent" | "unavailable"` — enum, NOT a bool. `present` = active non-superseded nutrition_target row exists for today; `absent` = `nutrition_target` table populated but no row covers today; `unavailable` = `nutrition_target` table is empty (no target ever set, OR W-C migration has not yet landed and the table doesn't exist — see acceptance test 4).

**Acceptance.**
1. Output shape per the findings doc §F-AV-01 example, with the addition of top-level `target_status: <enum>` and `is_partial_day_reason: <str>` per the typed contract above. The findings doc's example output predates the round-2 typed contract; PLAN §2.B is the source of truth (see F-PLAN-R2-04 for the findings-doc supersede note).
2. `is_partial_day` derives from `(local_now < end_of_day_cutoff) AND (meals_count < expected_for_day_complete)`. **Target-independent.** Cutoff configurable via thresholds; default `18:00` user-local.
3. `target_status` derivation: query `SELECT 1 FROM nutrition_target WHERE user_id=? AND status='active' AND superseded_by_target_id IS NULL AND effective_from <= ? LIMIT 1`. If row found → `present`. If query succeeds with no row AND table has any row for the user → `absent`. If query succeeds with no row AND table is empty for the user → `unavailable`. If table doesn't exist (W-C migration hasn't run) → `unavailable` with diagnostic flag (see acceptance test 4).
4. New test surface: `is_partial_day` true at 10:00 with 1 meal logged; false at 19:00 with 4 meals; transitions correctly across the cutoff. `target_status` cycles through `present` / `absent` / `unavailable` across four fixture states (active row covering today; row exists but doesn't cover today; table empty; table missing-because-pre-W-C). The pre-W-C case is the parallelization escape hatch — W-A can ship and be tested against a stub before W-C lands.

**W-D arm-1 contract (referenced from §2.E for clarity).** W-D arm-1 fires when `is_partial_day == true && target_status in ("absent", "unavailable")`. Treating `unavailable` as a no-target trigger is the v0.1.15 default (per OQ-7 ratification — see §8); the alternative (fail-closed, refuse-to-classify-until-target-set) is reversible if maintainer prefers.

### §2.C F-PV14-01 — CSV-fixture pull isolation marker

Inherited verbatim from `post_v0_1_14/carry_over_findings.md` §F-PV14-01. Default-deny CSV→canonical-state without `hai demo` marker or explicit `--allow-fixture-into-real-state` flag. Symmetric `--db-path` / `--base-dir` override rule. Capabilities-manifest source-type tagging.

**Acceptance.** Repro test: `hai pull --source garmin` against canonical DB without demo marker → USER_INPUT exit, zero rows in `sync_run_log`. Regression test: `hai stats` / `hai doctor` WARN when `last` and `for_date` diverge by >48h.

### §2.D W-C — `hai target nutrition` daily macro target commit

Inherited verbatim from `agent_state_visibility_findings.md` F-AV-03. New `nutrition_target` table + migration. New `hai target nutrition --kcal --protein-g --carbs-g --fat-g --phase --effective-from` command. **W57-gated:** agent can propose, user must commit per `hai target commit --target-id <id>`. Latest non-superseded row is active.

**Acceptance.** Schema migration test. W57 gate test: agent-proposed target row stays `proposed` until explicit user commit. Read-side test: `hai target list` returns active nutrition target. Integration: classifier (D arm-1 below) reads the active target row when classifying.

### §2.E W-D arm-1 — partial-day classification suppression (no-target only)

Inherited from `agent_state_visibility_findings.md` F-AV-04 arm 1 only. Arm 2 (end-of-day projection when target IS present) deferred to v0.1.17. **W-D arm-1 fires when `is_partial_day == true && target_status in ("absent", "unavailable")`** per the typed W-A contract (see §2.B and F-PLAN-R2-01 round-2 disposition). Treating `unavailable` (no target ever set, OR pre-W-C-migration table-missing) as a no-target trigger is the v0.1.15 default per OQ-7 maintainer ratification; behavior: emit `nutrition_status=insufficient_data` with reason `partial_day_no_target`. The runtime explicitly refuses to classify rather than misclassifying.

When `target_status == "present" && is_partial_day == true`, the classifier falls through to v0.1.17's W-D arm-2 logic. **Until arm-2 ships in v0.1.17**, the partial-day-with-target case falls back to today's behavior (classifies as if end-of-day) — this is a *known incomplete fix*; documented in §4.4 as a residual.

**Files of record:** `src/health_agent_infra/domains/nutrition/classify.py`, `src/health_agent_infra/domains/nutrition/policy.py`.

**Acceptance.**
1. Test: 10am breakfast-only intake (1344 kcal, partial-day) with `target_status="absent"` → `nutrition_status=insufficient_data`, reason `partial_day_no_target`. Currently misclassifies as `high_deficit` against config baseline.
2. Test: 10am breakfast-only with `target_status="unavailable"` (table empty) → same `insufficient_data` outcome (treats unavailable as no-target).
3. Test: 19:00 day-closed intake with any target_status → classifies normally (since `is_partial_day == false`).
4. Test: 10am breakfast-only with `target_status="present"` → falls through to existing classifier (until arm-2 lands in v0.1.17). Documented as known incomplete; arm-2 acceptance covers projection.
5. No call-graph changes to anything outside `domains/nutrition/`.

### §2.F W-E — skill update + optional morning-ritual skill

Inherited from `agent_state_visibility_findings.md` F-AV-05, with the `weigh_in` token explicitly excluded per F-PLAN-09 round-1 finding (W-B body-comp surface is deferred to v0.1.17, so `present.weigh_in.logged` cannot be truthy through any in-scope CLI path in v0.1.15).

**Required (small):** Update `merge-human-inputs/SKILL.md` to consume W-A presence tokens before composing prompts. Specifically: skill checks `present.{nutrition,gym,readiness,sleep}.logged` (note: `weigh_in` excluded — see below) and uses recap-first framing when true, forward-march framing when false.

**`weigh_in` handling (per F-PLAN-09).** W-A's `present` block emits `weigh_in: {logged: false, reason: "intake_surface_not_yet_implemented"}` consistently in v0.1.15 because `hai intake weight` (W-B) ships in v0.1.17. The skill explicitly does NOT branch on `weigh_in.logged` in v0.1.15. The morning-ritual skill (optional component below) may verbalize a weigh-in prompt to the user, but does not expect a state row in v0.1.15. **Open question OQ-1 below tracks whether to pull W-B forward if the foreign-user gate exposes friction without canonical weigh-in.**

**Optional (medium):** Ship a packaged `morning-ritual` skill that orchestrates pull → weigh-in prompt (verbal-only in v0.1.15) → breakfast prompt → plan, branching on W-A presence to choose framing. Decision per OQ below.

**Acceptance.**
1. Skill-test that asserts the skill reads from `hai intake gaps` and branches on `present.{nutrition,gym,readiness,sleep}.logged`.
2. Skill-test that asserts the skill does NOT branch on `present.weigh_in.logged` (defensive — surfaces if a future maintainer adds the check before W-B ships).
3. If morning-ritual skill ships: skill-test asserts the four-step orchestration order; weigh-in step verbalizes without state-write.

### §2.G W-2U-GATE — foreign-machine recorded session

Inherited from `v0_1_14/PLAN.md §2.A` with the load-bearing acceptance threshold restored verbatim per F-PLAN-05 round-1 finding (the round-1 PLAN had silently weakened it). Updated context: candidate package now includes W-A through W-E + W-GYM-SETID + F-PV14-01 fixes from this cycle.

**Candidate-package shape (per F-PLAN-06; OQ-8 ratified per Codex round-3).** Build wheel + sdist from the final v0.1.15 branch (post-merge to main commit). **Commit SHA recorded in the install record; no gate-candidate tag required.** Install the wheel into a clean Python 3.11+ environment on the foreign device. The foreign user's host agent (Claude Code or equivalent) runs against this installed package. No editable installs, no PyPI pre-release.

**Files of record:** `verification/dogfood/foreign_user/` (new); recorded session transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md`; state DB snapshot at `verification/dogfood/foreign_user/state_snapshot/<YYYY-MM-DD>/`; install record at `verification/dogfood/foreign_user/install_record_<YYYY-MM-DD>.json` (version, commit SHA, install command, environment hash).

**Acceptance — load-bearing thresholds (inherited from v0.1.14 PLAN §2.A):**
1. **One full session reaches `synthesized` with at most one brief in-session question to the maintainer.** Multiple interventions or any maintainer keyboard time = failure. (This is the v0.1.14 verbatim threshold; round-1 F-PLAN-05 restored it. Per F-PLAN-R2-05: any breach of this threshold is a **P0 gate failure** — the session must be re-run with the failure-cause fix applied, or the maintainer re-enters D14 to re-scope. P1 is reserved for trust-degrading findings that occur **within** the threshold-met session.)
2. Foreign user is non-maintainer. Maintainer presence: observe-only.
3. Recorded session transcript + install record + state DB snapshot all archived under the named paths above.
4. **No P0 finding is open at ship.** P0 = blocks `synthesized`, OR corrupts/drops user state, OR breaches the §2.G acceptance-1 session threshold (multiple interventions / maintainer keyboard time / >1 in-session question).
5. **All P1 findings closed if cheap (≤0.5 maintainer-day per finding) OR named-deferred to v0.1.16 with a specific destination.** P1 = within a threshold-met session: agent re-asks user for state already in DB, OR incorrect band classification the user notices, OR partial state corruption (silent intake drop), OR user has to read documentation mid-session.
6. **P2 findings defer to v0.1.16 unconditionally.** P2 = cosmetic, non-trust-affecting (typo in `hai today`, awkward phrasing, etc.).

**P-tier definitions (per F-PLAN-05 + F-PLAN-R2-05; ratify at D14 round-3 close):**
- **P0 — gate-blocking.** Any of: install failure; `hai pull` failure; `hai daily` failure; `hai today` returns no plan or wrong plan; **breach of acceptance-1 session threshold (multiple interventions / maintainer keyboard time / >1 in-session question)**; user state corruption or silent drop visible in-session.
- **P1 — trust-degrading but threshold met.** Any of: agent re-asks user for state already in DB (the W-A class), incorrect band classification the user notices, partial state corruption (silent intake drop discovered post-hoc), user has to read documentation mid-session. **All P1 findings occur within a session that satisfies acceptance-1**; if the threshold is breached, that's P0, not P1.
- **P2 — cosmetic.** Phrasing, typo, output-formatting, optional-flag confusion that doesn't block the workflow.
- **"Cheap" (P1 close-inline threshold)** = ≤0.5 maintainer-day, AND fix lands without re-running D14 audit, AND fix doesn't touch a state-model schema, AND fix doesn't change the capabilities manifest (per F-PLAN-R2-05 — capabilities manifest is the agent-contract surface; changes there are not inline-cheap regardless of LOC). P1 fixes that exceed any of these thresholds defer to v0.1.16 with named scope.

---

## 3. Cross-cutting work + governance edits

- **AGENTS.md D124-135** — update W-29 destination from "scheduled v0.1.15" → "scheduled v0.1.17." Note in the entry: "v0.1.15 → v0.1.17 redestination 2026-05-02 evening per scope-restructure round-0 self-audit (see `v0_1_15/PLAN.md` §1.4)."
- **AGENTS.md "Settled Decisions"** — candidate D-entry from W-A/W-C interaction (presence surface + target commit form the partial-day classification gate). Author CP at end of cycle if pattern repeats.
- **`reporting/docs/architecture.md`** — extend nutrition section with target-aware classification path (W-C + W-D arm-1).
- **`reporting/docs/state_model_v1.md`** — document `nutrition_target` table (W-C). `body_comp` (W-B) deferred to v0.1.17.
- **Capabilities manifest** — touched by W-A (extended `intake gaps` output shape), W-C (new `hai target nutrition`), F-PV14-01 (new `--allow-fixture-into-real-state` flag).
- **`tactical_plan_v0_1_x.md`** — rows 46-48 updated to reflect new v0.1.15 / v0.1.16 / v0.1.17 split.

---

## 4. Risks + hidden coupling

1. **W-A ↔ W-D arm-1 contract.** W-D arm-1 reads `is_partial_day` AND `target_status` from W-A's output. **Mitigation:** the round-1 PLAN had a contradictory predicate (F-PLAN-01); round-2 fixes by splitting the signals — `is_partial_day` is purely time/intake-based, `target_status` is a separate three-valued enum (`"present"` / `"absent"` / `"unavailable"`); the round-3 typed-contract fix per F-PLAN-R2-01 makes the enum explicit. W-D arm-1 fires on `is_partial_day && target_status in ("absent", "unavailable")`. Test fixtures cover all four states (present / absent / unavailable / table-missing-pre-W-C).
2. **W-C ↔ W-A `target_status` field.** W-A's `target_status` field reads from `nutrition_target` (W-C's table). **Mitigation:** W-A's read-side query catches `OperationalError` when the table doesn't exist (pre-W-C migration) and emits `target_status="unavailable"`; the empty-table case (table exists, no row covers today) returns `"absent"`; populated-with-active-row returns `"present"`. W-A and W-C land in Phase 1 in parallel; W-A's test fixtures stub the `nutrition_target` table state explicitly across the four cases so W-A is testable independently of W-C close.
3. **W-GYM-SETID — migration vs JSONL recovery boundary.** Per F-PLAN-07, the schema migration only rewrites set_ids for rows already in `gym_set`; rows that exist in JSONL but were dropped at intake (the maintainer's leg+back session has 8 such rows) are recoverable only via `hai state reproject --cascade-synthesis`. **Maintainer pre-gate procedure:** before Phase 3 opens, the maintainer (a) takes `hai backup` of their current state, (b) runs `hai state reproject --base-dir ~/.health_agent --cascade-synthesis` to recover the dropped sets, (c) re-runs `hai synthesize` to repopulate the synthesis-side tables. Foreign user starts from a fresh DB so the recovery path doesn't apply to them. Rollback for the maintainer: `hai restore` from the pre-procedure backup.
4. **W-D arm-1 / arm-2 known-incomplete fix.** Arm-1 (suppress when partial-day + no target) ships in v0.1.15; arm-2 (project end-of-day when partial-day + target) defers to v0.1.17. **Until arm-2 ships, the partial-day-with-target case falls back to today's classifier behavior** (classifies as if end-of-day). This is a *named incomplete fix*, not a silent partial-closure: §2.E acceptance test 3 explicitly asserts the fallback behavior.
5. **F-PV14-02 deferred — interim cleanup procedure (per F-PLAN-10 + F-PLAN-R2-06).** The carry-over doc paired F-PV14-01 (prevention) with F-PV14-02 (surgical cleanup tool). Deferring F-PV14-02 to v0.1.17 means: if a fixture leak recurs in v0.1.15 before F-PV14-01's prevention engages, the operator's only sanctioned cleanup paths are (a) **full point-in-time restore from a pre-leak `hai backup` bundle** via `hai restore --bundle <pre-leak.tar.gz>` (verified against `cli.py` — handler at `cmd_restore` lines 4289-4321; parser flags lines 8588-8599 accept only `--bundle` / `--db-path` / `--base-dir` and the handler overwrites the destination state.db + JSONL logs as a complete restore; there is **no selective restore**), or (b) **leave cosmetic `sync_run_log` rows in place** until F-PV14-02 ships in v0.1.17. **Raw SQL DELETE remains prohibited per AGENTS.md "Do Not Do."** A round-1 PLAN draft erroneously named "selective `hai restore`" as an option — Codex round-2 F-PLAN-R2-06 caught it; that surface does not exist. Foreign-user blast radius: low — F-PV14-01 prevents new contamination; existing contamination only affects maintainer's state, not the foreign-user's fresh DB.
6. **W-2U-GATE candidate dependency (per F-PLAN-11 — v0.1.15-specific procedure).** The foreign-user candidate must be on file by **Phase 0 close** (D11 bug-hunt complete; before Phase 1 opens). If no candidate at Phase 0 close: maintainer's options are (a) **hold the cycle open** and continue persona-runner / dogfood work until a candidate is named, then resume Phase 1; (b) **downgrade to a non-shipping candidate-package cycle** — ship Phase 1+2 fixes as v0.1.15 without the recorded session, defer W-2U-GATE to a new v0.1.16 (and re-D14 to formalize); (c) **defer the gate** with a new named destination (e.g. v0.1.18) and rename v0.1.15 + v0.1.16 + v0.1.17 accordingly. Path (a) is preferred. Note: this is *more aggressive* than v0.1.14's path 2 ("defer at pre-implementation gate") because v0.1.15's W-2U-GATE is the ship claim, not a Phase 1 workstream — there's nothing to "open implementation without" since the cycle's purpose IS the gate.

   **Candidate withdrawal mid-cycle (per round-2 OQ-9 + Codex round-3 ratification).** If a candidate is on file at Phase 0 close but withdraws between Phase 0 and Phase 3 (e.g., during Phase 1+2 implementation), the maintainer must re-enter the (a)/(b)/(c) decision tree above before opening Phase 3. The cycle is held; Phase 1+2 work that has already landed is preserved. No automatic shift to "ship without gate" — gate-test is the ship claim, so absence of a candidate at Phase 3 means the cycle either holds or downgrades, never silently ships. **Mid-Phase-3 abort case (per Codex round-3 OQ-9 opinion):** if the candidate begins the recorded session and aborts mid-stream, the existing acceptance-1 threshold already fails (no full session reaches `synthesized`); archive the partial transcript as non-gate evidence, fix/retry if the abort cause is product-side, OR re-enter §4.6 (a)/(b)/(c) if the candidate is no longer available.
7. **Sizing:** 16-25 days reflects round-1 finding F-PLAN-08 (round-1 PLAN had inconsistent ranges 14-20 / 13-22 / 14-18-23). Range widened by ~2-3 days for W-GYM-SETID JSONL-recovery acceptance + W-2U-GATE coordination overhead. Still tighter than v0.1.14 (30-43d closed at 35d). **Mitigation:** if D14 round-2 surfaces further sizing concerns, the cuts are reversible — pull individual deferred WS back from v0.1.17 (e.g. W-B if the gate exposes weigh-in friction; tracked in OQ-1).
8. **Dual-repo confusion.** A stale checkout exists at `/Users/domcolligan/Documents/health_agent_infra/`; the 2026-05-02 evening session was opened against that copy and rediscovered already-known bugs. **Mitigation:** D14 audit prompt Step 0 requires `pwd == /Users/domcolligan/health_agent_infra` AND rejects HEAD `2811669` (the stale-tree HEAD). AGENTS.md "Active repo path" note added per F-PLAN-12 — the discrimination is now part of the durable operating contract, not just per-prompt. Memory entry `feedback_verify_active_repo_at_session_start.md` saved.

---

## 5. Effort arithmetic (revised post-round-1 per F-PLAN-08)

| WS | Best | Mid | Worst | Δ vs round-1 |
|---|---|---|---|---|
| W-GYM-SETID | 1.5 | 2 | 3 | +0.5/+0.5/+1 (JSONL-recovery acceptance + fixture authoring per F-PLAN-07) |
| W-A | 2 | 2.5 | 3 | unchanged |
| F-PV14-01 | 1 | 1.5 | 2 | unchanged |
| W-C | 3 | 3.5 | 4 | unchanged |
| W-D arm-1 | 1 | 1.5 | 2 | unchanged (acceptance test 3 added but absorbs into existing budget) |
| W-E | 2 | 3 | 4 | unchanged (weigh_in exclusion is a one-line acceptance change) |
| W-2U-GATE | 4 | 5 | 7 | +1/+1/+2 (foreign-user coordination + inline P0/P1 fix risk per F-PLAN-08; threshold restoration adds session-rigor budget) |
| **Total** | **14.5** | **19** | **25** | +1.5/+1.5/+3 |

Adjusted for inter-WS coordination overhead (~5%): **16 - 20 - 26 days**, headlined as **16-25**.

D14 expectation: budget **2-4 rounds** per AGENTS.md empirical norm. Round 1 returned 12 findings (high-density round expected for substantive cycles with cross-doc consistency stakes); round 2 should drop to 4-7 if the halving signature holds; round 3 targets the 1-3 nit residual; round 4 only fires if round 3 surfaces structural issues (unlikely for a 7-WS cycle with no governance reversals).

---

## 6. Ship gates

Standard gates:
- Full pytest suite green (narrow + broader warning gates).
- `uvx mypy src/health_agent_infra` clean.
- `uvx bandit -ll -r src/health_agent_infra` clean.
- `uv run hai capabilities --json` round-trip stable.
- `uv run hai capabilities --markdown > reporting/docs/agent_cli_contract.md` regenerated and diffed.
- Persona matrix run (12-persona sweep on the post-W-A/C/D/E state model). P7..P12 only required if v0.1.17 W-Vb-4 hasn't shipped — otherwise skip the residual since it's not part of this cycle's claim.
- AGENTS.md D124-135 W-29 redestination edit landed (already landed in round-1 fan-out).
- AUDIT.md and CHANGELOG entries authored.
- Ship-time freshness checklist from AGENTS.md.

W-2U-GATE-specific gates (per F-PLAN-R2-07 — full §2.G contract restated here for ship-gate completeness):
- Recorded session shows non-maintainer foreign user reaching `synthesized` end-state on a fresh device.
- **Acceptance-1 threshold satisfied:** at most one brief in-session question to the maintainer; no multiple interventions; no maintainer keyboard time. (Breach = P0.)
- All P0 findings closed inline pre-ship.
- All P1 findings closed inline if cheap (≤0.5 maintainer-day, no D14 re-run, no state-model schema or capabilities-manifest touch) OR named-deferred to v0.1.16.
- All P2 findings deferred to v0.1.16.
- **Candidate-package archived:** wheel + sdist built from final v0.1.15 branch commit, install record at `verification/dogfood/foreign_user/install_record_<YYYY-MM-DD>.json` (commit SHA, install command, environment hash, Python version, OS, shell).
- Recorded session transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md`.
- State DB snapshot at `verification/dogfood/foreign_user/state_snapshot/<YYYY-MM-DD>/`.

---

## 7. What this PLAN does NOT cover

- **v0.1.16 scope:** empirical bug fixes from W-2U-GATE recorded session. P0 closed inline; P1 closed inline if cheap, otherwise named-deferred. P2+ defer unconditionally.
- **v0.1.17 scope:** maintainability + eval substrate consolidation. W-29 cli.py split + W-30 + W-AH-2 + W-AI-2 + W-AM-2 + W-Vb-4 + F-PV14-02 + W-B intake weight + W-D arm-2 projection. See `v0_1_17/README.md`.
- **v0.2.0 scope:** weekly review (W52) + deterministic factuality (W58D). Hard deps unchanged: v0.1.16 (foreign-user gate met) + v0.1.14 substrate (W-PROV-1 + W-AJ — already shipped). v0.1.17 is parallelizable with v0.2.0 since v0.2.0 does not depend on the eval-substrate expansion.
- **Capabilities-manifest schema freeze (W-30 destination):** unchanged at v0.2.3 per AGENTS.md D124-135.

---

## 8. Open questions for D14 round-3

**Closed by Codex round-2 audit (Codex opinion ratified by maintainer in round-2 fan-out):**
- **OQ-1 — W-B pull-forward.** CLOSED, defer W-B per Codex round-2 opinion: "v0.1.15 gate can be meaningful with verbalize-without-state-write as long as W-A always emits `weigh_in.logged=false` with the explicit unavailable reason and W-E never branches on it. Pull W-B forward only if the named candidate's day-1 workflow requires body-weight persistence." Reversible if Phase 0 candidate intake reveals body-weight persistence is required.
- **OQ-2 — W-GYM-SETID shape.** CLOSED in round-1 (prospective-only SQL migration; operator JSONL recovery). No further action.
- **OQ-3 — W-D arm-2 deferral.** CLOSED in round-1 (deferred to v0.1.17; arm-1 acceptance test 4 covers fallback). No further action.
- **OQ-4 — P-tier thresholds.** CLOSED in round-2 (overlap fixed per F-PLAN-R2-05; capabilities-manifest excluded from "cheap"; threshold breach = P0). Maintainer ratifies the new definitions at round-3 close.
- **OQ-5 — Round-0 self-audit pattern as D-entry.** CLOSED, do NOT promote yet per Codex round-2 opinion: "one successful restructure is not enough to promote it to a governance invariant. Record it as a lightweight validated pattern or CP candidate at v0.1.15 ship; promote to a D-entry after it recurs or after D14 explicitly needs it to prevent another over-scoped opening."
- **OQ-6 — Foreign-device OS.** CLOSED, single OS sufficient per Codex round-2 opinion: "one real foreign OS is enough for v0.1.15. The ship claim is 'a non-maintainer on a fresh device can reach `synthesized`', not 'all supported OSes are verified.' Record OS, Python version, shell, install command, environment hash in the install record. Multi-OS matrix belongs in later packaging/distribution hardening." Documented in §2.G + §6 install-record requirements.

**New open questions raised by round-2:**
- **OQ-7 (escalated from F-PLAN-R2-01).** `target_status="unavailable"` semantics for W-D arm-1 — does no-target-ever (or pre-W-C-table-missing) suppress classification (treat as `absent`) or fail-closed (refuse-to-classify-until-W-C-target-set)? **Round-2 PLAN default: treat as suppress trigger** (safer for the foreign user — same outcome as `absent`, no surprise hard-fail before the user has set targets). Maintainer to ratify; reversible.
- **OQ-8 (escalated from F-PLAN-R2-07).** Gate-candidate tag shape — commit SHA only (round-2 PLAN's choice), or a non-release gate tag (e.g. `gate/v0.1.15-YYYY-MM-DD`)? **Round-2 PLAN choice: commit SHA only**, since the install record carries it and a non-release tag adds bookkeeping without verification benefit. Maintainer to ratify.
- **OQ-9 (escalated from Codex round-2 closing OQ).** Candidate-withdrawal mid-cycle procedure — round-2 PLAN §4.6 adds "must re-enter (a)/(b)/(c) decision tree before opening Phase 3." Maintainer to ratify the wording or expand the procedure.

---

## 9. Provenance + evolution

- 2026-05-02 mid-day: original `v0_1_15/README.md` scoped hardening tier (W-29 + carry-overs only).
- 2026-05-02 evening (round 0): maintainer override expanded to 16 catalogued slots combining mechanical + daily-loop hardening + eval substrate + foreign-user gate combined.
- 2026-05-02 evening (round 0 self-audit → round 1): Claude-led audit against the second-user objective. Cut to 7 slots in v0.1.15; deferred 9 slots (W-D arm-2 + 8 others) to v0.1.17 (new).
- 2026-05-02 evening (round 1, initial): authored against the optimized scope. v0.1.16 stays reserved for empirical post-gate bugs. Codex D14 round-1 audit prompt authored.
- 2026-05-03 (D14 round-1 audit closed PLAN_COHERENT_WITH_REVISIONS): 12 findings; revisions applied in round-2 PLAN. Triage detail in `codex_plan_audit_response_response.md`.
- 2026-05-03 (round 2, initial): F-PLAN-01..12 from round-1 audit applied.
- 2026-05-03 (D14 round-2 audit closed PLAN_COHERENT_WITH_REVISIONS): 7 findings (F-PLAN-R2-01..07) at the empirical halving signature. Triage in `codex_plan_audit_round_2_response_response.md`.
- 2026-05-03 (round 3, initial): F-PLAN-R2-01 (W-A typed `target_status` enum) + F-PLAN-R2-02 (effort propagated across all surfaces) + F-PLAN-R2-03 (16-slot accounting unified) + F-PLAN-R2-04 (findings doc SUPERSEDED header note added; the in-doc F-AV-01 example was deliberately preserved as original-finding provenance, NOT rewritten) + F-PLAN-R2-05 (P0/P1 boundary clarified; threshold breach = P0; capabilities-manifest excluded from "cheap") + F-PLAN-R2-06 (selective-restore removed; truthful operator paths stated) + F-PLAN-R2-07 (ship-gate completeness with full §2.G contract restated) all applied. Codex round-2 opinions on OQ-1/5/6 ratified; new OQ-7/8/9 raised.
- 2026-05-03 (D14 round-3 audit closed PLAN_COHERENT_WITH_REVISIONS, recommended close-in-place): 3 nit-class findings (F-PLAN-R3-01..03). Halving signature held: 12 → 7 → 3. Triage in `codex_plan_audit_round_3_response_response.md`.
- 2026-05-03 (round 3 close, this PLAN): F-PLAN-R3-01 (PLAN §4 risks rewritten to use `target_status` not `target_present`) + F-PLAN-R3-02 (`tagged commit` removed from §2.G; tactical §5B P-tier matches PLAN §2.G) + F-PLAN-R3-03 (header status updated; F-PLAN-R2-11 nonexistent reference replaced with OQ-9 attribution; tactical typos fixed; restore citation expanded to handler + parser ranges) all applied. Codex round-3 opinions on OQ-7/8/9 ratified.
- **D14 closed in-place at round 3.** Phase 0 (D11) bug-hunt opens next per the substantive-cycle pattern.
