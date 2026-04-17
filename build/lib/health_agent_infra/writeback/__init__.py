"""WRITEBACK layer — schema-validated bounded local persistence."""

from health_agent_infra.writeback.recommendation import (
    ActionRecord,
    ALLOWED_RELATIVE_ROOT,
    perform_writeback,
)

__all__ = ["ActionRecord", "ALLOWED_RELATIVE_ROOT", "perform_writeback"]
