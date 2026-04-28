# Planning Tree — Reading Order Index

> **Last updated:** 2026-04-27 (post-v0.1.10 ship + strategic
> planning session).

This is the orientation guide to the `reporting/plans/` tree.
Read this when you're returning cold and need to find the right
doc by intent.

---

## I want to understand the project's strategic direction.

**Read in order:**

1. `strategic_plan_v1.md` — 12-24 month vision, settled decisions,
   five hypotheses, scope-expansion exploration.
2. `tactical_plan_v0_1_x.md` — concrete next 6-8 releases.
3. `risks_and_open_questions.md` — what could derail this + what
   decisions remain.

If you only have time for one: `strategic_plan_v1.md`.

## I want to scope the next release.

**Read in order:**

1. `tactical_plan_v0_1_x.md` § 2 — current release-in-flight.
2. `v0_1_11/PLAN.md` (or whichever cycle is open) — workstream
   contracts.
3. `v0_1_11/BACKLOG.md` — items deferred from prior cycle.
4. `v0_1_10/audit_findings.md` — last release's findings list.

If you only have time for one: `v0_1_11/PLAN.md`.

## I want to know how we evaluate correctness.

**Read in order:**

1. `eval_strategy/v1.md` — five eval classes, current coverage,
   ground-truth methodology.
2. `verification/dogfood/README.md` — persona harness operating
   guide.
3. `src/health_agent_infra/evals/rubrics/domain.md` — per-scenario
   rubric mechanics.

If you only have time for one: `eval_strategy/v1.md`.

## I want to know if the project is succeeding.

**Read in order:**

1. `success_framework_v1.md` — north-star, Tier 1-3 metrics,
   anti-metrics.
2. CHANGELOG.md (top entry) — what just shipped.

If you only have time for one: `success_framework_v1.md`.

## I want to understand what could go wrong.

**Read in order:**

1. `risks_and_open_questions.md` § 2-7 — strategic, technical,
   operational, external risks.

## I need to make a decision and don't want to commit.

**Read:**

1. `risks_and_open_questions.md` § 8 — open questions for
   maintainer judgement.
2. AGENTS.md "Settled Decisions" — what's already been decided.

## I'm a new agent session opening cold.

**Read in order:**

1. `AGENTS.md` (project root) — operating contract.
2. `README.md` (project root) — product story + quickstart.
3. `ARCHITECTURE.md` (project root) — runtime shape.
4. `REPO_MAP.md` (project root) — every directory classified.
5. `reporting/plans/strategic_plan_v1.md` — strategic frame.
6. `reporting/plans/tactical_plan_v0_1_x.md` — execution frame.

## I'm reviewing a specific past release.

Cycle directories preserve their own history:

- `v0_1_4/` — running activity pull (per memory).
- `v0_1_6/` — intervals.icu integration.
- `v0_1_7/` — auto manifest + W21 next-actions.
- `v0_1_8/` — plan-aware feedback visibility (W43, W48, W51).
- `v0_1_9/` — hardening + governance closure (B1-B8).
- `v0_1_10/` — pre-PLAN audit pattern + persona harness.
- `v0_1_11/` — audit-cycle deferred items + persona expansion (in flight).

Each cycle directory typically contains:
- `PLAN.md` — cycle scope.
- `audit_findings.md` (v0.1.10+) — pre-PLAN bug hunt findings.
- `BACKLOG.md` — items deferred from this cycle.
- `codex_audit_prompt.md` — external audit prompt.
- `codex_audit_response.md` (and round 2/3/4) — Codex findings.
- `RELEASE_PROOF.md` — ship readiness proof.
- `REPORT.md` — post-ship retro.

## Historical / superseded docs (preserve provenance, do not act on)

- `multi_release_roadmap.md` — **SUPERSEDED 2026-04-27** by
  `strategic_plan_v1.md` + `tactical_plan_v0_1_x.md`. Banner at top.
- `post_v0_1_roadmap.md` — earlier roadmap; superseded by the
  multi-release roadmap (2026-04-25), now further superseded.
- `agent_operable_runtime_plan.md` — Phase-3 design doc; some
  details lifted into AGENTS.md. Historical.
- `phase_0_findings.md`, `phase_0_5_synthesis_prototype.md`,
  `phase_2_5_*` — pre-v0.1 design exploration. Historical.
- `skill_harness_rfc.md` — pre-v0.1 RFC. Historical.
- `launch_notes.md` — pre-v0.1 launch checklist. Historical.

Do not assume claims in historical docs are still load-bearing.
Cross-check against AGENTS.md "Settled Decisions" if relying on
any of them.

## docs_overhaul/

The `docs_overhaul/` directory contains the v0.1.x documentation
restructuring work. Active when in-flight; check the directory's
own README for status.

---

## How to keep this index current

When a new doc is added or an old doc retired:

1. Add or remove the entry above.
2. Update the relevant cycle PLAN.md to reflect the doc relationship.
3. Bump the "Last updated" date at top.

This file is small enough that drift is the maintainer's
responsibility — no automated check today.
