# v0.1.15 cycle — workspace

**Status:** **D14 round 4 ready** (post-Phase-0 revision, 2026-05-03 evening). Round 1 PLAN_COHERENT_WITH_REVISIONS (12 findings); round 2 PLAN_COHERENT_WITH_REVISIONS (7); round 3 PLAN_COHERENT_WITH_REVISIONS (3 nits closed in-place); Phase 0 (D11) bug-hunt then surfaced **F-PHASE0-01 (revises-scope)** + 3 nits + persona matrix 13/13 clean (`audit_findings.md` + `pre_implementation_gate_decision.md`). F-PHASE0-01 Option A applied to PLAN.md §2.B/§2.D/§2.E/§4/§5 + nit fixes + cross-doc fan-out. **Round 4 codex audit prompt at `codex_plan_audit_round_4_prompt.md`.** Halving signature so far: 12 → 7 → 3 → ? (round-4 expected single-round close; small-surface revision).

**Tier:** substantive — see PLAN.md §1.4 for the scope-restructure provenance and §1.4 for the cycle-tier escalation triggers.

**Theme:** foreign-user candidate package + recorded gate session as ship claim.

## Reading order for the cycle session

1. `PLAN.md` (this directory) — open scope, 7 W-ids, 15-24 days estimated (revised round 4 per F-PHASE0-01 Option A; was 16-25 at round 3).
2. `AGENTS.md` — operating contract; pay attention to D124-135 (W-29 redestination — see PLAN.md §3) and D11 Phase 0 bug-hunt pattern.
3. `reporting/plans/README.md` — planning-tree reading-order index.
4. `reporting/plans/tactical_plan_v0_1_x.md` — v0.1.15 / v0.1.16 / v0.1.17 rows post-restructure.
5. `reporting/plans/post_v0_1_14/agent_state_visibility_findings.md` — W-A through W-E source detail.
6. `reporting/plans/post_v0_1_14/carry_over_findings.md` — F-PV14-01 detail.
7. `reporting/plans/v0_1_14/RELEASE_PROOF.md` and `v0_1_14_1/` — last-shipped state + W-2U-GATE inheritance chain.
8. `reporting/plans/v0_1_17/README.md` — what was deferred from this cycle's round-0 over-scoping.

## Scope provenance — three rounds in one evening + two D14 audit rounds

- **Mid-day round 0:** original "v0.1.15 = mechanical hardening only" framing per `agent_state_visibility_findings.md` recommendation. W-29 + carry-overs.
- **Evening round 0:** maintainer override expanded to 16 catalogued slots (W-D counted as two arms; mechanical + daily-loop hardening + eval substrate + foreign-user gate combined). 39-60 days.
- **Evening round 0 self-audit + round 1:** Claude-led audit against the second-user objective surfaced ~50% over-scoping. Maintainability + eval moved to **v0.1.17** (new). v0.1.15 stayed at 7 slots focused on the gate.
- **D14 round 1 (2026-05-03 morning):** Codex audit closed PLAN_COHERENT_WITH_REVISIONS, 12 findings. Maintainer applied 12/12 in PLAN round 2 + cross-doc fan-out (`tactical_plan_v0_1_x.md` §5B/§5C/§5D, `AGENTS.md` Do-Not-Do + active-repo declaration, `agent_state_visibility_findings.md` recommendation rewrite).
- **D14 round 2 (2026-05-03 mid-day):** Codex audit closed PLAN_COHERENT_WITH_REVISIONS, 7 findings (within the empirical halving range). Maintainer applied 7/7 in PLAN round 3 + cross-doc fan-out (typed `target_status` enum, effort propagation, F-PV14-02 selective-restore correction, ship-gate completeness).
- **D14 round 3 (2026-05-03 afternoon):** Codex audit closed PLAN_COHERENT_WITH_REVISIONS with 3 nit-class findings, recommended close-in-place. Maintainer applied 3/3 in PLAN final + minor cross-doc fan-out (tactical §5B P-tier alignment + typo + status; PLAN §4 risks rewritten to typed enum; PLAN §2.G "tagged commit" → "commit SHA"; restore citation expanded to handler + parser ranges). Halving signature: 12 → 7 → 3.
- **Phase 0 / D11 bug-hunt (2026-05-03 evening):** internal sweep + audit-chain probe + persona matrix (13/13 clean). Surfaced **F-PHASE0-01 (revises-scope)** — W-C `nutrition_target` table proposal duplicates the existing `target` table (migration 020, in tree since v0.1.8 W50). Plus 3 nits. Maintainer chose F-PHASE0-01 Option A (extend existing table). PLAN §2.B/§2.D/§2.E/§4/§5 + cross-doc fan-out applied. **D14 round 4 fires next.**

PLAN.md §1.4 + §9 record the scope-decision and audit-round provenance in detail.

## First actions for the cycle session

1. ✅ Read order above (this README is the entry point).
2. ✅ Author PLAN.md (done 2026-05-02 evening).
3. **NEXT:** Copy `_templates/codex_plan_audit_prompt.template.md` into this dir as `codex_plan_audit_prompt.md`. Customise the "Why this round" + step-1 reading list + step-2 audit questions for this cycle.
4. Hand both PLAN.md and codex_plan_audit_prompt.md to the maintainer for the Codex round-1 launch.

## D14 plan-audit settled expectation

Substantive tier with small W-id count (7) → 2-4 rounds expected per AGENTS.md empirical norm. Halving signature held end-to-end through round 3: 12 → 7 → 3, closed in-place. **Round 4 (post-Phase-0 F-PHASE0-01 ratification)** fires on a small-surface revision (§2.B/§2.D/§2.E/§4/§5 + 3 nit fixes); single-round close expected (PLAN_COHERENT or 1-2 nits close-in-place).

## Phase 0 (D11) scope

Substantive tier requires full Phase 0 bug-hunt: internal sweep + audit-chain probe + persona matrix + Codex external audit per the standard prompt template. Findings consolidate to `audit_findings.md` with `cycle_impact` tags. Phase 0 fires after D14 PLAN_COHERENT and before W-29 implementation opens — except W-29 isn't in this cycle, so Phase 0 fires before W-GYM-SETID + W-A (the first parallelizable Phase 1 workstreams).

## Implementation review settled expectation

Empirical settling: 3 rounds, 5→2→1-nit. Substantive tier; no shortcut to 2 rounds.

## Ship gates

See PLAN.md §6.

## Cross-references

- `PLAN.md` (open scope)
- `v0_1_17/README.md` (deferred work register)
- `post_v0_1_14/agent_state_visibility_findings.md`
- `post_v0_1_14/carry_over_findings.md`
- `_templates/codex_plan_audit_prompt.template.md`
- `_templates/codex_implementation_review_prompt.template.md`
