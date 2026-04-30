# v0.1.13 Carry-Over Register

**Date.** 2026-04-29 (authored at cycle open).
**Authored by.** Claude (delegated by maintainer).
**Source.** `reporting/plans/v0_1_12/RELEASE_PROOF.md` §5
("Out-of-scope items deferred with documented reason") +
`reporting/plans/v0_1_12/CARRY_OVER.md` §3 (reconciliation §6
v0.1.13+ named-defers).

This register is the W-CARRY workstream deliverable per
`reporting/plans/v0_1_13/PLAN.md` §2.C. Every named-defer from
v0.1.12 + every reconciliation §6 v0.1.13+ item has a row with
disposition.

---

## 1. v0.1.12 RELEASE_PROOF §5 named-defers

| Item | Disposition | W-id (this cycle) | Notes |
|---|---|---|---|
| **W-Vb persona-replay end-to-end** (proposal pre-population so `hai daily` reaches synthesis) | **in-cycle** | W-Vb (v0.1.13) | PLAN §2.A. Flips `apply_fixture()` to proposal-write branch + authors full-shape persona DomainProposal seeds + clean-wheel build-install-subprocess test. |
| **W-N-broader** (`-W error::Warning` gate fix — 49 + 1 sqlite3 connection-lifecycle leak sites) | **in-cycle** | W-N-broader (v0.1.13) | PLAN §2.A. Restore broader-gate ship target. Per-site fix table in eventual RELEASE_PROOF. |
| **W-FBC-2** (F-B-04 recovery prototype + multi-domain runtime enforcement) | **in-cycle** | W-FBC-2 (v0.1.13) | PLAN §2.A. Three sub-deliverables: recovery prototype, multi-domain rollout, optional per-domain fingerprint primitive. |
| **CP6 §6.3 framing edit application** | **in-cycle** | CP6 application (v0.1.13) | PLAN §2.A. Verbatim text edit per `v0_1_12/cycle_proposals/CP6.md` "Proposed delta." |

## 2. Reconciliation §6 v0.1.13+ items (from v0.1.12 CARRY_OVER §3)

| Item | Disposition | W-id (this cycle) | Notes |
|---|---|---|---|
| **A1 trusted-first-value rename + C7 acceptance matrix** | **in-cycle** | W-A1C7 (v0.1.13) | PLAN §2.C. First time the workstream is fully scoped (v0.1.12 named the deferral without per-W-id contract). |
| **A5 declarative persona expected-actions** (W-AK pulled forward from v0.1.14) | **in-cycle** | W-AK (v0.1.13) | PLAN §2.C. Precondition for v0.1.14 W58 prep. |
| **C2 / W-LINT regulated-claim lint** | **in-cycle** | W-LINT (v0.1.13) | PLAN §2.C. First surface; lands before v0.2.0 weekly review. |
| **W-29-prep cli.py boundary audit** | **in-cycle** | W-29-prep (v0.1.13) | PLAN §2.C. Per CP1; parser/capabilities regression test mandatory regardless of split decision. |
| **L3 §6.3 strategic-plan framing edit (CP6)** | **in-cycle** *(also covered by §1)* | CP6 application (v0.1.13) | Cross-reference row added at D14 round 1 per F-PLAN-02. The reconciliation source row (`v0_1_12/CARRY_OVER.md` §3 line 58) maps to the same CP6-application workstream that v0.1.12 RELEASE_PROOF §5 line names; recorded in §1 above as the inheritance entry. Listed here too so this register's acceptance check #2 (every reconciliation §6 v0.1.13+ row disposed) is honest. |
| **W-FBC-2 (full F-B-04 multi-domain closure)** | **in-cycle** *(also covered by §1)* | W-FBC-2 (v0.1.13) | Cross-reference row added at D14 round 1 per F-PLAN-02. The reconciliation source row (`v0_1_12/CARRY_OVER.md` §3 line 59 — "new W-id introduced by Codex F-PLAN-R2-04 in this cycle") maps to the same W-FBC-2 workstream that v0.1.12 RELEASE_PROOF §5 names; recorded in §1 above as the inheritance entry. Listed here too for honest acceptance-check coverage. |

## 3. Originally-planned v0.1.13 scope (tactical_plan §4.1)

These were scoped to v0.1.13 in the tactical plan authored
2026-04-27. Listed here for traceability — they're not
"carry-over" in the v0.1.12 sense, but they ARE part of v0.1.13
in-cycle scope, and a fresh agent reading the carry-over register
will look here for the full opening scope.

| Item | Disposition | W-id (this cycle) | Source |
|---|---|---|---|
| First-time-user onboarding flow | in-cycle | W-AA | tactical §4.1 |
| `hai capabilities --human` mode | in-cycle | W-AB | tactical §4.1 |
| README rewrite | in-cycle | W-AC | tactical §4.1 |
| Error-message quality pass | in-cycle | W-AD | tactical §4.1 |
| `hai doctor` expansion (incl. F-DEMO-01 detection prevention) | in-cycle | W-AE | tactical §4.1 + F-DEMO-01 prevention |
| README quickstart smoke test | in-cycle | W-AF | tactical §4.1 |
| `hai today` cold-start prose | in-cycle | W-AG | tactical §4.1 |

## 4. Reconciliation §6 v0.1.14+ items (named-defer pass-through)

These remain deferred to later cycles. Listed for traceability.

| Item | Defer to | Reason |
|---|---|---|
| **W-Vb-3** persona-replay extension to P9/P11/P12 | v0.1.14 | fork-deferred at D14 round 1 per F-PLAN-06; v0.1.13 W-Vb closes P1+P4+P5 fully, P9/P11/P12 named here in honest partial-closure-naming convention (AGENTS.md "Patterns the cycles have validated"). New row added 2026-04-30. |
| W-29 cli.py mechanical split | v0.1.14 | per CP1, conditional on W-29-prep verdict |
| L2 W-DOMAIN-SYNC scoped contract test | v0.1.14 | per Codex F-PLAN-09 |
| A12 judge-adversarial fixtures | v0.1.14 | folds into W-AI |
| A2/W-AL calibration scaffold | v0.1.14 | schema/report shape only |
| W-30 capabilities-manifest schema freeze | v0.2.0 | per CP2 |
| MCP server *plan* | v0.3 | per CP4 |
| MCP read-surface ship | v0.4 or v0.5 | per CP4 |
| W52 / W53 / W58 (weekly review + insight ledger + factuality gate) | v0.2.0 | strategic plan Wave 2 |

## 5. Pre-cycle ships absorbed in this PLAN

| Item | Where shipped | W-id (catalogue completeness) |
|---|---|---|
| **W-CF-UA** (intervals.icu Cloudflare User-Agent block fix) | **v0.1.12.1 hotfix** (branchpoint `v0.1.12` tag, three commits, lightweight RELEASE_PROOF at `reporting/plans/v0_1_12_1/RELEASE_PROOF.md`) | W-CF-UA (v0.1.13 PLAN §1.2 catalogue D — completeness only, NOT a v0.1.13 deliverable) |

The fix is also present in the `cycle/v0.1.13` branch via cherry-
pick from `hotfix/v0.1.12.1` (commit 636f5d3 carries the code +
test diff; commit a10a238 carries the lightweight RELEASE_PROOF
doc, cherry-picked in at D14 round 1 per F-PLAN-03 to make the
in-tree provenance citation honest). The hotfix branch + the cycle
branch both carry the identical code change at the file level; the
hotfix branch additionally carries the version bump (0.1.12 →
0.1.12.1) + CHANGELOG hotfix entry, neither of which propagates
into the cycle branch (cycle/v0.1.13 will eventually bump to 0.1.13).

## 6. Phase 0 (D11) findings absorbed

**Phase 0 not yet run.** Will run after this PLAN reaches
`PLAN_COHERENT` per Codex D14 audit. Section will be filled in by
the W-CARRY workstream at cycle close, populated from
`audit_findings.md`.

## 7. Audit-chain integrity (cycle open)

- v0.1.12 demo isolation contract holds (validated at v0.1.12 ship;
  re-verify in Phase 0).
- 12-persona matrix at v0.1.12 ship: 0 findings, 0 crashes; re-run
  in Phase 0.
- Bandit `-ll` baseline at v0.1.12 ship: 46 Low, 0 Medium, 0 High.
  v0.1.13 target: ≤ 50 Low (D10), 0 Medium / High preserved.
- Capabilities byte-stability holds at v0.1.12 ship; will be locked
  by W-29-prep regression test in v0.1.13.

## 8. Settled-decision deltas expected at v0.1.13 ship

No new D-entries planned. CP6 (deferred application) lands as a
strategic-plan §6.3 verbatim edit; this is a wording change, not a
new settled decision. The four-element load-bearing-whole framing
is the substance.

W-29-prep produces the verdict that v0.1.14 W-29 gates on; the
verdict (split / do-not-split / split-with-revisions) is recorded
in v0.1.13 RELEASE_PROOF and may add a v0.1.14 rider in AGENTS.md
"Settled Decisions" but not a new D-entry.

---

## Acceptance check (W-CARRY)

- [ ] Every line in `v0_1_12/RELEASE_PROOF.md` §5 has a disposition
  row in §1 above.
- [ ] Every reconciliation §6 v0.1.13+ item from `v0_1_12/CARRY_OVER.md`
  §3 has a row in §2 above.
- [ ] Phase 0 findings absorbed in §6 (filled at cycle close).
- [ ] Pre-cycle ships (W-CF-UA) recorded in §5 with branchpoint +
  artifact references.

W-CARRY workstream deliverable: this document + acceptance checks
ticked at cycle close.
