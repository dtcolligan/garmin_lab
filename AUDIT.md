# Audit Cycle

Health Agent Infra uses structured Codex review before substantive releases.
The review is not a badge; the artifact is the value. This file indexes the
existing release-cycle audit records so they are visible from the repo root.

## v0.1.14.1 - 2026-05-02

Garmin-live unreliability surfaced as a structured signal in the
capabilities manifest. `hai capabilities --json` now exposes
`flags[].choice_metadata` with a `garmin_live → {reliability:
"unreliable", reason: ..., prefer_instead: "intervals_icu"}` block on
both `hai pull --source` and `hai daily --source`; `_resolve_pull_source`
emits a single stderr warning when the resolved source is `garmin_live`.
Single workstream (W-GARMIN-MANIFEST-SIGNAL); purely additive — manifest
`schema_version` unchanged. **Tier:** hardening.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit | (skipped per D15 hardening latitude) | n/a |
| Implementation review | (skipped per D15 hardening latitude — internal sweep + test gates were the ship evidence) | n/a |

**Outcome:** Shipped as a hardening cycle without an external Codex
audit round. Test surface: 2581 passed, 3 skipped (+15 vs v0.1.14).
Broader-warning gate (`-W error::Warning`) clean. Mypy 0 errors @ 127
source files. Bandit 46 Low / 0 Medium / 0 High (unchanged from v0.1.14
baseline). Ruff clean on modified files. Capabilities snapshot
regenerated; diff is purely additive (two `choice_metadata` blocks).
Release proof:
[`reporting/plans/v0_1_14_1/RELEASE_PROOF.md`](reporting/plans/v0_1_14_1/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_14_1/REPORT.md`](reporting/plans/v0_1_14_1/REPORT.md).

## v0.1.14 - 2026-05-01

Eval substrate + provenance + recovery path. 13 W-ids at PLAN open
(post-W-2U-GATE-defer): 8 closed, 3 partial-closed with named v0.1.15
destinations (W-AH / W-AI / W-Vb-3), 2 deferred (W-2U-GATE / W-29),
1 absorbed (W-AM into W-AI). Pre-implementation gate invoked PLAN.md
§1.3.1 path 2 to defer W-2U-GATE foreign-machine onboarding empirical
proof (no candidate on file at gate). **Tier:** substantive.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_14/codex_plan_audit_response.md) (+ rounds 2-4; settled at PLAN_COHERENT round 4 with 12 → 7 → 3 → 1-nit → CLOSE signature; 23 cumulative findings, all ACCEPT) | rounds 1-4 |
| Implementation review 1-3 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_14/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES, 7 findings) → [`codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_2_response.md) (round 2 SHIP_WITH_FIXES, 2 findings) → [`codex_implementation_review_round_3_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_3_response.md) (round 3 SHIP_WITH_NOTES, 1 nit) | [`codex_implementation_review_round_1_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_1_response.md) → [`codex_implementation_review_round_2_response_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_2_response_response.md) → [`codex_implementation_review_round_3_response_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_3_response_response.md) |

**Outcome:** `SHIP_WITH_NOTES` in implementation round 3 with the
F-IR-R3-01 nit applied. Settling shape `7 → 2 → 1-nit` mirrors
v0.1.12 (`5 → 2 → 0`) + v0.1.13 (`6 → 2 → 0`); 10 cumulative IR
findings, all ACCEPT. Test surface: 2566 passed, 3 skipped (+73 vs
v0.1.13). All ship gates green: pytest broader, mypy 0 @ 127,
bandit 46 Low / 0 Med / 0 High, ruff clean, capabilities byte-stable
post-snapshot regen for the named-change-accepted W-AN + W-BACKUP +
W-PROV-1 surfaces. Release proof:
[`reporting/plans/v0_1_14/RELEASE_PROOF.md`](reporting/plans/v0_1_14/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_14/REPORT.md`](reporting/plans/v0_1_14/REPORT.md).

## v0.1.13 - 2026-04-30

Largest cycle in the v0.1.x track at 17 workstreams. Three parallel themes:
close v0.1.12 named-deferred items (W-Vb persona-replay end-to-end ship-set,
W-N-broader 50-site sqlite3 leak fix, W-FBC-2 multi-domain F-B-04 closure,
CP6 §6.3 strategic-plan edit), ship the originally-planned onboarding scope
(W-AA `hai init --guided`, W-AB `hai capabilities --human`, W-AC README
rewrite, W-AD USER_INPUT prose, W-AE `hai doctor --deep`, W-AF README smoke,
W-AG `hai today` cold-start prose), land governance prerequisites
(W-29-prep cli.py boundary audit, W-LINT regulated-claim lint, W-AK
declarative persona expected-actions, W-A1C7 acceptance matrix). Cycle-order
inversion: IR ran *before* RELEASE_PROOF authoring. **Tier:** substantive.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-5 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_13/codex_plan_audit_response.md) (+ rounds 2-5; settled at PLAN_COHERENT round 5 with 11 → 7 → 3 → 1-nit → 0 signature) | rounds 1-5 |
| Implementation review 1-3 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_13/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES, 6 findings) → [`codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_2_response.md) (round 2 SHIP_WITH_FIXES, 2 findings) → [`codex_implementation_review_round_3_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_3_response.md) (round 3 SHIP, 0 findings) | [`codex_implementation_review_round_1_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_1_response.md) → [`codex_implementation_review_round_2_response_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_2_response_response.md) |

**Outcome:** `SHIP` in implementation round 3. 16 of 17 W-ids closed-this-cycle;
1 partial-closure (W-Vb, P1+P4+P5 ship-set with 9-persona residual fork-deferred
to v0.1.14 W-Vb-3). Test surface: 2493 passed, 3 skipped (+109 vs v0.1.12).
Broader-warning gate (`-W error::Warning`) restored as the v0.1.13 ship target.
Release proof:
[`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_13/REPORT.md`](reporting/plans/v0_1_13/REPORT.md).

## v0.1.12 - 2026-04-29

Carry-over closure + trust repair. No release-blocker workstream by design.
Ten workstreams across docs / governance / per-domain code / mypy / demo
packaging. Settled D15 (cycle-weight tiering: substantive / hardening /
doc-only / hotfix). Six cycle proposals (CP1-CP6) authored.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_12/codex_plan_audit_response.md) (+ rounds 2-4; settled at PLAN_COHERENT round 4 with 10 → 5 → 3 → 0 signature) | rounds 1-4 |
| Implementation review 1-2 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_12/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES) → round 2 SHIP_WITH_NOTES | rounds 1-2 |

**Outcome:** `SHIP_WITH_NOTES` in implementation round 2. 8 of 10 W-ids
shipped, 2 partial-closures (W-Vb, W-FBC), 1 named-fork (W-N-broader). Test
surface: 2384 passed, 2 skipped (+37 vs v0.1.11). Release proof:
[`reporting/plans/v0_1_12/RELEASE_PROOF.md`](reporting/plans/v0_1_12/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_12/REPORT.md`](reporting/plans/v0_1_12/REPORT.md).

A v0.1.12.1 hotfix shipped 2026-04-29 to address a Cloudflare User-Agent
block on the intervals.icu pull adapter (W-CF-UA). See
[`reporting/plans/v0_1_12_1/RELEASE_PROOF.md`](reporting/plans/v0_1_12_1/RELEASE_PROOF.md).

## v0.1.11 - 2026-04-28

Audit-cycle deferred items closed (W-B/E/F/H/K/L/N/Q/R), persona matrix
expanded 8 → 12, property-based tests for the policy DSL, demo isolation
contract shipped (boundary-stop replay). Settled D13 (threshold-injection
seam trusted-by-design) + D14 (pre-cycle Codex plan-audit pattern).

| Round | Audit prompt | Codex response | Maintainer response |
|---|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_prompt.md`](reporting/plans/v0_1_11/codex_plan_audit_prompt.md) | [`codex_plan_audit_response.md`](reporting/plans/v0_1_11/codex_plan_audit_response.md) (+ rounds 2-4) | rounds 1-4 |
| Implementation review 1-4 | (D14-revised PLAN.md) | rounds 1-4 | rounds 1-4 |

**Outcome:** `SHIP` in implementation round 4. 19 of 20 W-ids shipped;
W-Vb named-deferred to v0.1.12. Test surface: 2347 passed, 2 skipped
(+145 vs v0.1.10). Release proof:
[`reporting/plans/v0_1_11/RELEASE_PROOF.md`](reporting/plans/v0_1_11/RELEASE_PROOF.md).

## v0.1.10 - 2026-04-27

Pre-PLAN bug-hunt phase introduced (D11), persona harness landed, mypy +
bandit correctness pass, write-surface guard. First cycle to run a
structured audit phase before plan authoring.

**Outcome:** `SHIP_WITH_NOTES`. Audit findings consolidated to
[`reporting/plans/v0_1_10/audit_findings.md`](reporting/plans/v0_1_10/audit_findings.md);
all `in-scope` findings absorbed; deferred items carry to v0.1.11. Release
proof: [`reporting/plans/v0_1_10/RELEASE_PROOF.md`](reporting/plans/v0_1_10/RELEASE_PROOF.md).

## v0.1.9 - 2026-04-26

Hardening and governance closure after parallel Codex + Claude reviews of
the v0.1.8 surface. Scope is B1-B8 only: W57 archive/commit gates,
fail-loud skill overlay, validator shape hardening, direct synthesize parity,
pull/clean provenance, safety-skill prose, and small P2 hygiene.

| Round | Audit prompt | Maintainer response |
|---|---|---|
| Implementation review | [`codex_audit_prompt.md`](reporting/plans/v0_1_9/codex_audit_prompt.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_9/codex_implementation_review_response.md) |

**Outcome:** `SHIP_WITH_FIXES` review findings accepted and fixed. Full
suite: 2133 passed, 2 skipped. Release proof:
[`reporting/plans/v0_1_9/RELEASE_PROOF.md`](reporting/plans/v0_1_9/RELEASE_PROOF.md).

Report: [`reporting/plans/v0_1_9/REPORT.md`](reporting/plans/v0_1_9/REPORT.md).

## v0.1.8 - 2026-04-25

Plan-aware feedback visibility: intent + target + data-quality ledgers,
code-owned review-summary tokens, four new `hai stats` modes, config
validate + diff, `hai daily --auto --explain`, and synthesis-skill scoring.

| Round | Audit prompt | Codex response | Maintainer response |
|---|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_8/codex_audit_prompt.md) | [`codex_audit_response.md`](reporting/plans/v0_1_8/codex_audit_response.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_8/codex_implementation_review_response.md) |
| 2 | See response | [`codex_implementation_review_round2_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round2_response.md) | [`codex_implementation_review_response_round2.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round2.md) |
| 3 | See response | [`codex_implementation_review_round3_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round3_response.md) | [`codex_implementation_review_response_round3.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round3.md) |
| 4 | See response | [`codex_implementation_review_round4_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round4_response.md) | [`codex_implementation_review_response_round4.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round4.md) |

**Outcome:** `SHIP_WITH_NOTES` in round 4. Net: +129 tests in the
release proof, W57 deactivation hardening, and bool-as-int defence in depth
for review-summary thresholds. Deferred notes are tracked in
[`reporting/plans/v0_1_9/BACKLOG.md`](reporting/plans/v0_1_9/BACKLOG.md).
Release proof:
[`reporting/plans/v0_1_8/RELEASE_PROOF.md`](reporting/plans/v0_1_8/RELEASE_PROOF.md).

## v0.1.7 - 2026-04-25

First-class agent flow and calibrated correctness.

| Round | Audit prompt | Response |
|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_7/codex_audit_prompt.md) | [`codex_audit_response.md`](reporting/plans/v0_1_7/codex_audit_response.md) |

**Outcome:** `SHIP`. Release proof:
[`reporting/plans/v0_1_7/RELEASE_PROOF.md`](reporting/plans/v0_1_7/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_7/REPORT.md`](reporting/plans/v0_1_7/REPORT.md).

## v0.1.6 - 2026-04-25

Migration-drift hardening, explicit proposal replacement semantics,
intervals.icu-as-default-source, and packaged-skills install.

| Round | Audit prompt | Response |
|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_6/codex_audit_prompt.md) | [`internal_audit_response.md`](reporting/plans/v0_1_6/internal_audit_response.md) |
| 2 | [`codex_audit_prompt_round2.md`](reporting/plans/v0_1_6/codex_audit_prompt_round2.md) | [`codex_audit_response_round2.md`](reporting/plans/v0_1_6/codex_audit_response_round2.md) |
| Implementation review | [`codex_implementation_review_prompt.md`](reporting/plans/v0_1_6/codex_implementation_review_prompt.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_6/codex_implementation_review_response.md) |

**Outcome:** `SHIP` after maintainer-owned revision plan
[`reporting/plans/v0_1_6/codex_v0_1_6_improvement_plan.md`](reporting/plans/v0_1_6/codex_v0_1_6_improvement_plan.md).

## v0.1.4 And Earlier

Pre-formal-cycle. Audit material lives under per-release folders without a
standardized round structure. The stronger pattern stabilized across
v0.1.6-v0.1.8.

## How A Round Works

1. The maintainer drafts `PLAN.md`.
2. A fresh Codex session reviews the plan or implementation diff.
3. Findings are classified by severity and tied to file/line evidence.
4. The maintainer replies with fixes, explicit deferrals, or disagreement.
5. Review repeats until the release reaches `SHIP` or `SHIP_WITH_NOTES`.
6. `RELEASE_PROOF.md` records version, tests, generated-contract state, and
   known deferrals.

The cycle exists because this is a single-maintainer project with a
high-value invariant: the code-vs-skill boundary must not decay under
release pressure.
