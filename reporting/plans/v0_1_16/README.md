# v0.1.16 cycle — workspace

**Status:** scoped as **empirical-by-design**, not yet open. PLAN.md is intentionally NOT authored ahead of cycle open — its scope IS the post-gate findings from v0.1.15's W-2U-GATE recorded session, which cannot be pre-scoped honestly.

**Tier (anticipated):** substantive. Empirical post-gate cycles typically close 4-9 days but the cycle pattern still fires full Phase 0 + multi-round D14 because what's being audited is the gate-output triage, not a fixed workstream catalogue.

**Provenance.** Created 2026-05-03 alongside the v0.1.15 D14 close. The 2026-05-02 evening scope-restructure folded the original-v0.1.16 "first foreign-machine onboarding empirical proof" claim INTO v0.1.15 (where the gate session is the ship claim) and reassigned this cycle to "empirical post-gate bug fixes only" per the maintainer's stated framing: "v0.1.16 cycle should literally just be bug fixes from the onboarding tests." Maintainability + eval substrate that the v0.1.15 round-0 PLAN tried to graft into v0.1.15 was reassigned to v0.1.17 instead.

## Why no PLAN.md yet

The v0.1.15 round-0 over-scoping (16 catalogued slots; D14 round-1 cut to 7 against the second-user objective) showed the cost of forward-speculation. v0.1.16's scope is literally "the bugs the foreign-user gate session surfaces" — authoring a PLAN.md before the session fires would either be (a) speculative scope (guessing what bugs will appear), or (b) trivial restate of "TBD per gate output." Neither helps. The PLAN authors when the cycle opens, with the gate-session transcript and the W-2U-GATE deferral list as inputs.

## Scope (provisional, finalised in PLAN.md after gate)

| W-id (anticipated) | Title | Source |
|---|---|---|
| **W-2U-FIX-P1** | All P1 fixes named-deferred from v0.1.15's recorded session | v0.1.15 W-2U-GATE output |
| **W-2U-FIX-P2** | All P2 fixes from the recorded session (or named further deferrals) | v0.1.15 W-2U-GATE output |
| **W-EXPLAIN-UX-2** | Empirical foreign-user pass over `hai explain` consuming v0.1.14 review doc's `carries-forward-to-v0.1.15` section | v0.1.14 W-EXPLAIN-UX |

**Effort estimate (anticipated):** 4-9 days. Bounded by the gate-session output cap (~10 P-class findings if the v0.1.15 candidate package is reasonably prepared). If the gate surfaces a structural-blocker P0 wave that exceeds inline-fix budget, v0.1.15 holds rather than ships, and v0.1.16 reshapes around the held cycle.

## Hard dependencies

- **v0.1.15 must close** with `W-2U-GATE` recorded-session signed-off (non-maintainer reached `synthesized` under acceptance-1 threshold; P0 closed inline).
- v0.1.15 transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md` must exist.
- v0.1.15 install record + state DB snapshot archived per v0.1.15 PLAN §6 ship gates.
- All P1 findings the v0.1.15 cycle named-deferred to v0.1.16 must have specific destinations (per v0.1.15 PLAN §2.G acceptance — "named-deferred to v0.1.16 with a specific destination").

## What's explicitly OUT of scope for v0.1.16

- **No new feature work.** Empirical fixes only.
- **No mechanical refactor** (W-29 cli.py split, W-30) — those live in v0.1.17.
- **No eval-substrate work** (W-AH-2 / W-AI-2 / W-AM-2) — those live in v0.1.17.
- **No persona-replay residual** (W-Vb-4) — v0.1.17.
- **No state-model schema additions** (W-B body-comp, W-D arm-2 projection) — v0.1.17.
- **No v0.2.x scope.**

If a finding from the gate session reveals a need for one of the above, **the maintainer's call is whether to (a) defer that finding to v0.1.17 / v0.2.x with named scope, or (b) hold v0.1.16 open and re-open v0.1.15 to re-do the gate** — not silently absorb it.

## First actions for the cycle session (when it opens)

1. Confirm v0.1.15 closed (RELEASE_PROOF.md + REPORT.md present in `v0_1_15/`).
2. Read v0.1.15's gate-session transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md`.
3. Read v0.1.15's RELEASE_PROOF.md §carry-overs (named-deferred P1 list).
4. Confirm `pwd == /Users/domcolligan/health_agent_infra` per the AGENTS.md active-repo declaration.
5. Author `PLAN.md` per the empirical findings. First line: tier annotation. Sections: theme + per-finding W-id + ship gates + risks. Each named-deferred P1 from v0.1.15 becomes a W-2U-FIX-P1 sub-item.
6. Copy `_templates/codex_plan_audit_prompt.template.md` and customise for the empirical-cycle audit shape (D14 questions focus on whether the empirical findings are correctly triaged, not whether the workstream catalogue is right).
7. Hand to maintainer for D14 round-1 launch.

## D14 plan-audit settled expectation (empirical cycles)

Substantive tier still applies. Empirical cycles tend to settle in 2-3 rounds (the catalogue is bounded by gate output; less surface area for cross-doc consistency findings than v0.1.15's restructure).

## Phase 0 (D11) scope (empirical cycles)

Substantive tier requires Phase 0, but for an empirical cycle the bug-hunt is narrower: re-run the persona matrix against the post-v0.1.15 state model, audit-chain probe to verify v0.1.15's W-2U-GATE artifacts are still queryable, internal sweep on the named-deferred P1 fix surfaces. Codex external bug-hunt audit is optional per maintainer.

## Ship gate

- All v0.1.15 named-deferred P1 findings either fixed or re-deferred with a specific v0.1.17 / v0.2.0 destination.
- All gate-session P2 findings fixed or deferred.
- W-EXPLAIN-UX-2 dispositions filed against the v0.1.14 review doc's carries-forward section.
- Standard substantive-cycle gates (pytest, mypy, bandit, capabilities round-trip).
- AUDIT.md + CHANGELOG entries authored.
- Ship-time freshness checklist from AGENTS.md.

## Cross-references

- `reporting/plans/v0_1_15/PLAN.md` §2.G (W-2U-GATE acceptance + P-tier definitions; this cycle inherits the named-deferred P1 list).
- `reporting/plans/tactical_plan_v0_1_x.md` row 47 + §5C.
- `reporting/plans/v0_1_17/README.md` (the next cycle; non-empirical, knowable scope).
