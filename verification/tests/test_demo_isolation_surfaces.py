"""W-Va: demo isolation across the full persistence surface.

Per Codex F-PLAN-02 + maintainer answer Q-2: demo mode must isolate
the DB, the writeback/intake base_dir (`~/.health_agent`), and the
user config (`thresholds.toml`). Real persistence surfaces stay
byte-identical across an entire demo session.

This file owns the cross-resolver isolation contract. Lifecycle +
fail-closed + matrix tests live elsewhere.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from health_agent_infra.core.config import user_config_path
from health_agent_infra.core.demo.session import (
    close_session,
    open_session,
)
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.state.store import resolve_db_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _checksum_tree(root: Path) -> str:
    """Recursive hash of every file under root. Used to assert byte-stability."""
    if not root.exists():
        return f"<absent:{root}>"
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode("utf-8"))
            h.update(b":")
            h.update(path.read_bytes())
            h.update(b"\n")
    return h.hexdigest()


@pytest.fixture
def real_dirs(tmp_path, monkeypatch):
    """Set the real DB and base_dir paths to tmp-controlled locations.

    Pytest can't actually run against the user's real ~/.health_agent
    without polluting it. So we redirect the "real" paths to tmp_path
    sub-trees that we own; the test assertions remain valid because
    they verify these "real" paths stay byte-identical when a demo
    is active.
    """
    real_root = tmp_path / "real"
    real_db = real_root / "state.db"
    real_base = real_root / "base"
    real_marker_path = tmp_path / "demo_marker.json"

    real_db.parent.mkdir(parents=True)
    real_base.mkdir(parents=True)

    monkeypatch.setenv("HAI_STATE_DB", str(real_db))
    monkeypatch.setenv("HAI_BASE_DIR", str(real_base))
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(real_marker_path))

    return {
        "real_db": real_db,
        "real_base": real_base,
        "real_marker_path": real_marker_path,
    }


# ---------------------------------------------------------------------------
# Resolver routes scratch when marker valid
# ---------------------------------------------------------------------------


def test_resolve_db_path_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = resolve_db_path()
        assert resolved == marker.db_path
        assert resolved != real_dirs["real_db"]
    finally:
        close_session()


def test_resolve_base_dir_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = resolve_base_dir()
        assert resolved == marker.base_dir_path
        assert resolved != real_dirs["real_base"]
    finally:
        close_session()


def test_user_config_path_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = user_config_path()
        assert resolved == marker.config_path
    finally:
        close_session()


# ---------------------------------------------------------------------------
# Resolver routes real when no marker
# ---------------------------------------------------------------------------


def test_resolve_db_path_real_when_no_marker(real_dirs):
    assert resolve_db_path() == real_dirs["real_db"]


def test_resolve_base_dir_real_when_no_marker(real_dirs):
    assert resolve_base_dir() == real_dirs["real_base"]


# ---------------------------------------------------------------------------
# Real-tree byte-stability across an open / close cycle
# ---------------------------------------------------------------------------


def test_real_persistence_byte_identical_across_session(real_dirs, tmp_path):
    """Open a session, write a file via the scratch resolvers, close. Real tree stable."""
    # Pre-populate the real surfaces with arbitrary content so the
    # checksum has bytes to compare.
    real_dirs["real_db"].write_bytes(b"REAL DB CONTENT v0")
    (real_dirs["real_base"] / "real_jsonl.jsonl").write_text(
        '{"line": 1}\n'
    )
    pre_db = real_dirs["real_db"].read_bytes()
    pre_base = _checksum_tree(real_dirs["real_base"])

    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)

    # Simulate work writing to scratch surfaces.
    marker.db_path.write_bytes(b"SCRATCH DB CONTENT")
    (marker.base_dir_path / "scratch_jsonl.jsonl").write_text(
        '{"line": "demo"}\n'
    )

    # Real surfaces unchanged mid-session.
    assert real_dirs["real_db"].read_bytes() == pre_db
    assert _checksum_tree(real_dirs["real_base"]) == pre_base

    close_session()

    # And after close.
    assert real_dirs["real_db"].read_bytes() == pre_db
    assert _checksum_tree(real_dirs["real_base"]) == pre_base
