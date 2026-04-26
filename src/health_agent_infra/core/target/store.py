"""Target ledger CRUD layer (v0.1.8 W50). Mirrors the intent ledger
shape (W49) — replacements use archive/supersession, never destructive
UPDATE; outcomes never auto-mutate targets.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional


_TARGET_COLUMNS = (
    "target_id",
    "user_id",
    "domain",
    "target_type",
    "status",
    "value_json",
    "unit",
    "lower_bound",
    "upper_bound",
    "effective_from",
    "effective_to",
    "review_after",
    "reason",
    "source",
    "ingest_actor",
    "created_at",
    "supersedes_target_id",
    "superseded_by_target_id",
)


_VALID_STATUS = {"proposed", "active", "superseded", "archived"}
_VALID_TARGET_TYPE = {
    "hydration_ml", "protein_g", "calories_kcal",
    "sleep_duration_h", "sleep_window", "training_load",
    "other",
}


@dataclass
class TargetRecord:
    target_id: str
    user_id: str
    domain: str
    target_type: str
    status: str
    value: Any
    unit: str
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    effective_from: date
    effective_to: Optional[date]
    review_after: Optional[date]
    reason: str
    source: str
    ingest_actor: str
    created_at: datetime
    supersedes_target_id: Optional[str]
    superseded_by_target_id: Optional[str]

    def to_row(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "target_type": self.target_type,
            "status": self.status,
            "value_json": json.dumps({"value": self.value}, sort_keys=True),
            "unit": self.unit,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": (
                self.effective_to.isoformat()
                if self.effective_to is not None
                else None
            ),
            "review_after": (
                self.review_after.isoformat()
                if self.review_after is not None
                else None
            ),
            "reason": self.reason,
            "source": self.source,
            "ingest_actor": self.ingest_actor,
            "created_at": self.created_at.isoformat(),
            "supersedes_target_id": self.supersedes_target_id,
            "superseded_by_target_id": self.superseded_by_target_id,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "TargetRecord":
        d = dict(row)
        value_json = d.get("value_json") or "{}"
        decoded = json.loads(value_json)
        return cls(
            target_id=d["target_id"],
            user_id=d["user_id"],
            domain=d["domain"],
            target_type=d["target_type"],
            status=d["status"],
            value=decoded.get("value", decoded),
            unit=d["unit"],
            lower_bound=d.get("lower_bound"),
            upper_bound=d.get("upper_bound"),
            effective_from=date.fromisoformat(d["effective_from"]),
            effective_to=(
                date.fromisoformat(d["effective_to"])
                if d.get("effective_to") is not None
                else None
            ),
            review_after=(
                date.fromisoformat(d["review_after"])
                if d.get("review_after") is not None
                else None
            ),
            reason=d.get("reason", ""),
            source=d["source"],
            ingest_actor=d["ingest_actor"],
            created_at=datetime.fromisoformat(d["created_at"]),
            supersedes_target_id=d.get("supersedes_target_id"),
            superseded_by_target_id=d.get("superseded_by_target_id"),
        )


class TargetValidationError(ValueError):
    """Raised when a candidate target row fails the documented invariants."""


def _validate(record: TargetRecord) -> None:
    if record.status not in _VALID_STATUS:
        raise TargetValidationError(
            f"target.status must be one of {_VALID_STATUS}; got {record.status!r}"
        )
    if record.target_type not in _VALID_TARGET_TYPE:
        raise TargetValidationError(
            f"target.target_type must be one of {_VALID_TARGET_TYPE}; got {record.target_type!r}"
        )
    if (
        record.effective_to is not None
        and record.effective_to < record.effective_from
    ):
        raise TargetValidationError(
            "target.effective_to must not precede effective_from"
        )
    if (
        record.lower_bound is not None
        and record.upper_bound is not None
        and record.lower_bound > record.upper_bound
    ):
        raise TargetValidationError(
            "target.lower_bound must not exceed upper_bound"
        )
    # v0.1.8 W57 / Codex P1-2 invariant: agent-proposed targets MUST
    # land as `proposed`. They become `active` only via an explicit
    # user-confirmed `commit_target` call, never via insert.
    if record.source != "user_authored" and record.status == "active":
        raise TargetValidationError(
            f"target.source={record.source!r} requires status='proposed' on insert; "
            f"only 'user_authored' may land directly as 'active'. "
            f"Use commit_target() to promote a proposed row."
        )


def add_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: str,
    target_type: str,
    value: Any,
    unit: str,
    effective_from: date,
    effective_to: Optional[date] = None,
    review_after: Optional[date] = None,
    lower_bound: Optional[float] = None,
    upper_bound: Optional[float] = None,
    status: str = "active",
    reason: str = "",
    source: str = "user_authored",
    ingest_actor: str = "cli",
    target_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> TargetRecord:
    """Persist a new target row. Returns the materialised record."""

    when = now or datetime.now(timezone.utc)
    record = TargetRecord(
        target_id=target_id or f"target_{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        domain=domain,
        target_type=target_type,
        status=status,
        value=value,
        unit=unit,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        effective_from=effective_from,
        effective_to=effective_to,
        review_after=review_after,
        reason=reason,
        source=source,
        ingest_actor=ingest_actor,
        created_at=when,
        supersedes_target_id=None,
        superseded_by_target_id=None,
    )
    _validate(record)
    row = record.to_row()
    cols = ", ".join(_TARGET_COLUMNS)
    placeholders = ", ".join("?" for _ in _TARGET_COLUMNS)
    conn.execute(
        f"INSERT INTO target ({cols}) VALUES ({placeholders})",
        tuple(row[c] for c in _TARGET_COLUMNS),
    )
    conn.commit()
    return record


def list_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
) -> list[TargetRecord]:
    """Return every target row matching the filters, oldest first."""

    sql = "SELECT * FROM target WHERE user_id = ?"
    params: list[Any] = [user_id]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    if target_type is not None:
        sql += " AND target_type = ?"
        params.append(target_type)
    sql += " ORDER BY created_at, target_id"
    return [TargetRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def list_active_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
    domain: Optional[str] = None,
) -> list[TargetRecord]:
    """Active target rows whose effective window covers ``as_of_date``."""

    sql = (
        "SELECT * FROM target "
        "WHERE user_id = ? "
        "  AND status = 'active' "
        "  AND effective_from <= ? "
        "  AND (effective_to IS NULL OR effective_to >= ?)"
    )
    params: list[Any] = [user_id, as_of_date.isoformat(), as_of_date.isoformat()]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY domain, target_type, created_at, target_id"
    return [TargetRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def commit_target(
    conn: sqlite3.Connection,
    *,
    target_id: str,
    user_id: str,
) -> bool:
    """Promote a `proposed` target row to `active`. The W57-required
    user-gated commit path for agent-proposed rows.

    Returns True when a matching proposed row was found and promoted,
    False otherwise. Idempotent.

    Codex R2-2 invariant: when the row being committed has
    ``supersedes_target_id`` set, atomically flip the superseded
    parent to ``status='superseded'`` in the same transaction. This
    is the deferred deactivation that ``supersede_target`` skipped
    for agent-proposed replacements.
    """

    row = conn.execute(
        "SELECT supersedes_target_id FROM target "
        "WHERE target_id = ? AND user_id = ? AND status = 'proposed'",
        (target_id, user_id),
    ).fetchone()
    if row is None:
        return False

    parent_id = row["supersedes_target_id"]

    cursor = conn.execute(
        "UPDATE target SET status = 'active' "
        "WHERE target_id = ? AND user_id = ? AND status = 'proposed'",
        (target_id, user_id),
    )
    if cursor.rowcount > 0 and parent_id is not None:
        conn.execute(
            "UPDATE target SET status = 'superseded', "
            "superseded_by_target_id = ? "
            "WHERE target_id = ? AND user_id = ?",
            (target_id, parent_id, user_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def archive_target(
    conn: sqlite3.Connection,
    *,
    target_id: str,
    user_id: str,
) -> bool:
    cursor = conn.execute(
        "UPDATE target SET status = 'archived' "
        "WHERE target_id = ? AND user_id = ?",
        (target_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def supersede_target(
    conn: sqlite3.Connection,
    *,
    old_target_id: str,
    new_record: TargetRecord,
) -> TargetRecord:
    """Insert a replacement target linked to ``old_target_id``.

    Codex R2-2 invariant: an agent cannot deactivate a user's
    existing active row without explicit user commit. Same shape as
    ``supersede_intent``:

    - User-authored supersede flips the old row immediately.
    - Agent-proposed supersede inserts the new row as proposed +
      links ``supersedes_target_id`` to the old row, but leaves the
      old row alone. ``commit_target`` performs the atomic
      deactivate-on-promotion when the user commits.
    """

    new_record.supersedes_target_id = old_target_id
    _validate(new_record)
    row = new_record.to_row()
    cols = ", ".join(_TARGET_COLUMNS)
    placeholders = ", ".join("?" for _ in _TARGET_COLUMNS)
    conn.execute(
        f"INSERT INTO target ({cols}) VALUES ({placeholders})",
        tuple(row[c] for c in _TARGET_COLUMNS),
    )
    if new_record.source == "user_authored":
        conn.execute(
            "UPDATE target SET status = 'superseded', "
            "superseded_by_target_id = ? "
            "WHERE target_id = ?",
            (new_record.target_id, old_target_id),
        )
    conn.commit()
    return new_record
