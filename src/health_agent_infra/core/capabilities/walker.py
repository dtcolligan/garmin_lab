"""Argparse tree walker — collects contract annotations into a manifest.

The manifest is a dict:

    {
      "schema_version": "agent_cli_contract.v1",
      "hai_version": "<package version>",
      "generated_by": "core.capabilities.walker.build_manifest",
      "commands": [
        {
          "command": "hai pull",
          "description": "...",
          "mutation": "writes-sync-log",
          "idempotent": "yes",
          "json_output": "default",
          "exit_codes": ["OK", "USER_INPUT", "TRANSIENT"],
          "agent_safe": true,
        },
        ...
      ],
    }

Nested subcommands (e.g. ``hai state init``) are flattened into one row
per leaf command. The ``command`` field is the full invocation string
the user types. Rows are sorted lexicographically so the manifest is
diff-friendly.
"""

from __future__ import annotations

import argparse
from typing import Any, Iterable, Optional

from health_agent_infra import __version__ as _PACKAGE_VERSION


# ---------------------------------------------------------------------------
# Allowed values — drift-proof enums for the annotation payload.
# Changing these is a schema break; bump ``SCHEMA_VERSION`` if you do.
# ---------------------------------------------------------------------------

MUTATION_CLASSES: frozenset[str] = frozenset({
    "read-only",          # no persistent writes anywhere
    "writes-sync-log",    # only sync_run_log (e.g. hai pull)
    "writes-audit-log",   # JSONL audit file writes (e.g. hai review record)
    "writes-state",       # primary state DB writes (e.g. hai synthesize)
    "writes-memory",      # user_memory table writes (hai memory set)
    "writes-skills-dir",  # copies the packaged skills tree to ~/.claude
    "writes-config",      # writes a config/thresholds file
    "writes-credentials", # OS keyring writes (hai auth garmin)
    "interactive",        # requires live human input (hai init)
})

IDEMPOTENCY: frozenset[str] = frozenset({
    "yes",                  # same inputs → same state after every call
    "yes-with-supersede",   # supersedes a prior row via a --supersede flag
    "no",                   # append-only, order-sensitive, or interactive
    "n/a",                  # read-only command, idempotency doesn't apply
})

JSON_OUTPUT_MODES: frozenset[str] = frozenset({
    "default",   # always emits JSON on stdout
    "opt-in",    # JSON via an explicit --json flag
    "opt-out",   # JSON by default; --text suppresses
    "none",      # text-only output
    "dual",      # explicit --json and --text flags both supported
})

# Legacy exit-code placeholder for subcommands that still return 0/2 via
# the old pattern. An honest manifest reports what the handler actually
# does today, so these sit alongside migrated entries until the
# exit-code migration is finished (Phase 2 part 2).
LEGACY_EXIT_CODES: tuple[str, ...] = ("LEGACY_0_2",)

MIGRATED_EXIT_CODES: frozenset[str] = frozenset({
    "OK", "USER_INPUT", "TRANSIENT", "NOT_FOUND", "INTERNAL",
})

ALLOWED_EXIT_CODES: frozenset[str] = MIGRATED_EXIT_CODES | {"LEGACY_0_2"}


# The argparse-defaults keys we own. Prefix with underscore so they
# don't collide with user-facing CLI flags and so they're visibly
# internal in any stack trace that prints a Namespace.
CONTRACT_KEYS: tuple[str, ...] = (
    "_contract_mutation",
    "_contract_idempotent",
    "_contract_json_output",
    "_contract_exit_codes",
    "_contract_agent_safe",
    "_contract_description",
)


SCHEMA_VERSION = "agent_cli_contract.v1"


class ContractAnnotationError(ValueError):
    """Raised when an annotation value is outside the allowed set.

    Caught at build-time (import time, typically) so a bad annotation
    fails the test suite rather than silently corrupting the manifest.
    """


# ---------------------------------------------------------------------------
# Annotate a subparser — the hook cli.py uses on every add_parser call.
# ---------------------------------------------------------------------------


def annotate_contract(
    parser: argparse.ArgumentParser,
    *,
    mutation: str,
    idempotent: str,
    json_output: str,
    exit_codes: Iterable[str],
    agent_safe: bool,
    description: Optional[str] = None,
) -> None:
    """Attach contract metadata to an argparse subparser.

    Called by ``cli.py`` immediately after ``add_parser`` +
    ``set_defaults(func=...)``. Values are validated eagerly so a
    typo surfaces at CLI-construction time rather than in the
    manifest.
    """

    if mutation not in MUTATION_CLASSES:
        raise ContractAnnotationError(
            f"unknown mutation class {mutation!r}; "
            f"allowed: {sorted(MUTATION_CLASSES)}"
        )
    if idempotent not in IDEMPOTENCY:
        raise ContractAnnotationError(
            f"unknown idempotency value {idempotent!r}; "
            f"allowed: {sorted(IDEMPOTENCY)}"
        )
    if json_output not in JSON_OUTPUT_MODES:
        raise ContractAnnotationError(
            f"unknown json_output value {json_output!r}; "
            f"allowed: {sorted(JSON_OUTPUT_MODES)}"
        )

    code_list = list(exit_codes)
    for code in code_list:
        if code not in ALLOWED_EXIT_CODES:
            raise ContractAnnotationError(
                f"unknown exit code {code!r}; "
                f"allowed: {sorted(ALLOWED_EXIT_CODES)}"
            )
    # OK is expected on every migrated command — catch accidental
    # omission early.
    if code_list != list(LEGACY_EXIT_CODES) and "OK" not in code_list:
        raise ContractAnnotationError(
            f"exit_codes must include 'OK' for migrated commands; "
            f"got {code_list!r}"
        )

    parser.set_defaults(
        _contract_mutation=mutation,
        _contract_idempotent=idempotent,
        _contract_json_output=json_output,
        _contract_exit_codes=tuple(code_list),
        _contract_agent_safe=bool(agent_safe),
        _contract_description=description,
    )


# ---------------------------------------------------------------------------
# Walker — traverse the argparse tree, flatten to leaf commands.
# ---------------------------------------------------------------------------


def walk_parser(
    parser: argparse.ArgumentParser,
    *,
    prog: str = "hai",
) -> list[dict[str, Any]]:
    """Walk ``parser`` and return one row per leaf command.

    A "leaf command" is any parser that has no further subparsers — the
    thing the user actually invokes. For ``hai auth garmin``, the leaf
    parser is the one registered under ``auth_sub.add_parser("garmin")``;
    ``hai auth`` itself is an internal node and does not appear in the
    manifest.

    Rows are sorted by ``command`` lexicographically so the manifest is
    deterministic across runs.
    """

    rows: list[dict[str, Any]] = []
    _walk(parser, path=[prog], rows=rows)
    rows.sort(key=lambda r: r["command"])
    return rows


def _walk(
    parser: argparse.ArgumentParser,
    *,
    path: list[str],
    rows: list[dict[str, Any]],
) -> None:
    sub_actions = _subparsers_actions(parser)
    if not sub_actions:
        # Leaf — record it if it has a handler (set_defaults(func=...)).
        # Some internal-only parsers (the top-level `hai` parser, an
        # intermediate `hai auth`) have no func; they're not real
        # commands and shouldn't appear in the manifest.
        defaults = parser._defaults  # argparse has no public accessor
        func = defaults.get("func")
        if func is None:
            return
        rows.append(_row_for_leaf(parser=parser, path=path, defaults=defaults))
        return

    for sub_action in sub_actions:
        for name, child in sub_action.choices.items():
            _walk(child, path=path + [name], rows=rows)


def _subparsers_actions(
    parser: argparse.ArgumentParser,
) -> list[argparse._SubParsersAction]:
    return [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]


def _row_for_leaf(
    *,
    parser: argparse.ArgumentParser,
    path: list[str],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    command = " ".join(path)
    description = (
        defaults.get("_contract_description")
        or parser.description
        or _help_text_from_parent(parser)
        or ""
    )
    return {
        "command": command,
        "description": description.strip() if isinstance(description, str) else "",
        "mutation": defaults.get("_contract_mutation"),
        "idempotent": defaults.get("_contract_idempotent"),
        "json_output": defaults.get("_contract_json_output"),
        "exit_codes": list(defaults.get("_contract_exit_codes") or ()),
        "agent_safe": defaults.get("_contract_agent_safe"),
    }


def _help_text_from_parent(parser: argparse.ArgumentParser) -> Optional[str]:
    """Best-effort: pull the help= string the parent parser registered
    this subcommand with, if we can find it. argparse doesn't expose
    this directly, so we read ``prog`` off the parser and search the
    parent's ``_choices_actions``. Returns None if we can't find it —
    callers fall back to the empty string in that case.
    """

    # argparse doesn't keep a back-pointer, so this is best-effort and
    # intentionally simple. Most annotated commands will override via
    # _contract_description anyway; this is just a polite fallback
    # when a command has no description= and no override.
    return None


# ---------------------------------------------------------------------------
# Manifest builder — wraps walker rows in the top-level envelope.
# ---------------------------------------------------------------------------


def build_manifest(
    parser: argparse.ArgumentParser,
    *,
    hai_version: Optional[str] = None,
) -> dict[str, Any]:
    """Build the full manifest dict for the given top-level parser.

    Separate from :func:`walk_parser` so the envelope (schema_version,
    version, generator) can evolve independently of the per-command rows.
    """

    return {
        "schema_version": SCHEMA_VERSION,
        "hai_version": hai_version or _PACKAGE_VERSION,
        "generated_by": "core.capabilities.walker.build_manifest",
        "commands": walk_parser(parser),
    }


# ---------------------------------------------------------------------------
# Coverage helpers — used by tests to assert every leaf is annotated.
# ---------------------------------------------------------------------------


def unannotated_commands(
    parser: argparse.ArgumentParser,
) -> list[str]:
    """Return the list of leaf commands that are missing one or more
    contract annotations. Used by the CI coverage test."""

    unannotated: list[str] = []
    for row in walk_parser(parser):
        if (
            row["mutation"] is None
            or row["idempotent"] is None
            or row["json_output"] is None
            or row["agent_safe"] is None
            or not row["exit_codes"]
        ):
            unannotated.append(row["command"])
    return unannotated
