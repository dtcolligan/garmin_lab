"""`hai eval run` CLI wrappers.

Registered on the top-level ``hai`` dispatcher in
:mod:`health_agent_infra.cli`. This module has no side effects at
import time.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .runner import (
    EvalRunError,
    SUPPORTED_DOMAINS,
    load_scenarios,
    run_scenarios,
)


def cmd_eval_run(args: argparse.Namespace) -> int:
    if args.synthesis:
        kind = "synthesis"
        domain: Optional[str] = None
    else:
        kind = "domain"
        domain = args.domain

    from health_agent_infra.core import exit_codes

    try:
        scenarios = load_scenarios(kind, domain=domain)
    except EvalRunError as exc:
        print(f"eval error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    if not scenarios:
        print(
            f"no scenarios found for kind={kind!r} domain={domain!r}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    try:
        scores = run_scenarios(scenarios)
    except EvalRunError as exc:
        print(f"eval error: {exc}", file=sys.stderr)
        return exit_codes.INTERNAL

    total = len(scores)
    passed = sum(1 for s in scores if s.passed)
    failed = total - passed

    if args.json:
        payload = {
            "kind": kind,
            "domain": domain,
            "total": total,
            "passed": passed,
            "failed": failed,
            "scores": [s.to_dict() for s in scores],
        }
        print(json.dumps(payload, indent=2))
    else:
        header = f"{kind}" + (f" / {domain}" if domain else "")
        print(f"eval {header}: {passed}/{total} passed ({failed} failed)")
        for s in scores:
            mark = "PASS" if s.passed else "FAIL"
            print(f"  [{mark}] {s.scenario_id}")
            if not s.passed:
                for axis, verdict in s.axes.items():
                    if verdict == "fail":
                        diff = s.diffs.get(axis, {})
                        print(f"      - {axis}: FAIL {diff}")

    # Scenario pass/fail outcome: OK when everything passed, USER_INPUT
    # when at least one failed — failed scenarios indicate a rubric /
    # runtime delta the caller can investigate, not a runtime crash.
    return exit_codes.OK if failed == 0 else exit_codes.USER_INPUT


def register_eval_subparser(sub: argparse._SubParsersAction) -> None:
    """Register the ``hai eval`` subparser tree on an existing dispatcher."""

    p_eval = sub.add_parser(
        "eval",
        help="Run evaluation scenarios against the deterministic runtime",
    )
    eval_sub = p_eval.add_subparsers(dest="eval_command", required=True)

    p_run = eval_sub.add_parser(
        "run",
        help="Execute scenarios for a domain or the synthesis layer",
    )
    group = p_run.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--domain",
        choices=sorted(SUPPORTED_DOMAINS),
        help="Run domain-level (classify + policy) scenarios for this domain",
    )
    group.add_argument(
        "--synthesis",
        action="store_true",
        help="Run synthesis-level (X-rule + run_synthesis) scenarios",
    )
    p_run.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text",
    )
    p_run.set_defaults(func=cmd_eval_run)
    # Contract annotation — kept local to the eval module so the
    # packaged wheel's eval surface stays self-describing. The wider
    # capabilities module tolerates annotations anywhere in the tree.
    from health_agent_infra.core.capabilities import annotate_contract
    annotate_contract(
        p_run,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",
        exit_codes=("OK", "USER_INPUT", "INTERNAL"),
        agent_safe=True,
        description=(
            "Execute frozen deterministic eval scenarios for a domain "
            "(--domain) or the synthesis layer (--synthesis). Read-only "
            "— scores scenarios, never writes state. USER_INPUT when a "
            "scenario fails its rubric; INTERNAL if the runner itself "
            "crashes."
        ),
    )
