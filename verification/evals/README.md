# Evaluation framework — v1

The eval framework ships **inside the package** at
`src/health_agent_infra/evals/` (runner + CLI + scenarios + rubrics). A
wheel install of `health_agent_infra` therefore carries the full eval
surface, and `hai eval run` works from any working directory without
requiring a repo checkout.

This directory retains only the dev-reference docs:

- `README.md` — this file.
- `skill_harness_blocker.md` — the deferred-follow-up record for the
  skill-narration axis.

## Where everything now lives

    src/health_agent_infra/evals/
        __init__.py
        runner.py            # scenario loader + scorer
        cli.py               # `hai eval run` argparse entry point
        scenarios/
            recovery/        # domain scenarios
            running/
            sleep/
            stress/
            strength/
            nutrition/
            synthesis/       # X-rule + run_synthesis scenarios
        rubrics/
            domain.md
            synthesis.md

## What this evaluates

- **Domain layer** — `classify.py` + `policy.py` per domain. Scored
  against expected classified bands, forced actions, capped
  confidences, and rule-id firings.
- **Synthesis layer** — `core/synthesis.py` + `core/synthesis_policy.py`.
  Scored against expected X-rule firings (by rule id), final per-domain
  actions, final confidences, and any authored validation-error or
  synthesis-error invariants.

## What this deliberately does NOT evaluate

- **Skill narration quality.** Rationale prose, uncertainty prose,
  joint-narration conflict resolution, and any other behaviour that
  lives inside `skills/<name>/SKILL.md` requires invoking Claude Code
  (or equivalent agent runtime) as a subprocess. Per Phase 2.5 Track B
  Condition 3 this is a deferred follow-up; scenarios carry a
  `rationale_quality: skipped_requires_agent_harness` axis so the gap
  is visible rather than silently green.

- **Live Garmin pull.** Evals run on frozen evidence bundles; the
  pull path is covered by `verification/tests/test_pull_garmin_live.py`
  with a mocked client.

See `skill_harness_blocker.md` for the deferred skill-harness work.

## CLI

    hai eval run --domain recovery          # run all recovery scenarios
    hai eval run --synthesis                # run all synthesis scenarios
    hai eval run --domain recovery --json   # machine-readable output

Exit code is 0 when all loaded scenarios pass, 1 when any fails, 2 on
usage error. The command is registered unconditionally on every install
of the package.
