"""Intake layer — structured + free-text user-reported facts.

Phase 7C. This module houses per-domain intake helpers: typed parsing,
validation at the CLI boundary, and append-only JSONL audit logging. The
CLI (``hai intake <kind>``) plumbs user-supplied data through these helpers
before invoking the projectors in ``health_agent_infra.state.projector``
that land the rows in the DB.

Pattern mirrors ``writeback/`` and ``review/``: validation + JSONL audit
is the durable boundary; DB projection is a best-effort queryable view
that ``hai state reproject --base-dir`` can rebuild from the JSONL.
"""
