"""Protocol for flagship pull adapters feeding recovery_readiness_v1.

This Protocol captures the *thin* flagship contract: a named source and a
deterministic loader that returns evidence in the dict shape
``clean.health_model.recovery_readiness_v1.clean.clean_inputs`` consumes.

It is deliberately narrower than the broader multi-source platform contract
at ``reporting/docs/source_adapter_contract_v1.md``, which governs adapters
that emit the full canonical artifact family (``source_record``,
``provenance_record``, ``sleep_daily``, ``readiness_daily``,
``training_session``, ``daily_health_snapshot``). The flagship slice does
not require that broader emission; it consumes a thin dict and does not
produce canonical artifacts. The two contracts serve different layers and
do not conflict.

Conformance is structural. No inheritance is required. See
``pull/garmin/recovery_readiness_adapter.py::GarminRecoveryReadinessAdapter``
for the reference conformer.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class FlagshipPullAdapter(Protocol):
    """Minimum contract for a pull adapter feeding the flagship loop.

    Conformers must:

      - expose a stable ``source_name`` attribute (string), used for
        provenance, logs, and operator-facing identification.
      - provide a ``load(as_of)`` method that returns a dict compatible
        with ``clean_inputs()`` — specifically keys ``sleep``,
        ``resting_hr``, ``hrv``, and ``training_load``.

    The Protocol intentionally does not encode the full dict shape in the
    type system; runtime compatibility with ``clean_inputs`` is the
    binding contract. This keeps the Protocol a thin adapter-level
    interface rather than a second schema.
    """

    source_name: str

    def load(self, as_of: date) -> dict:
        ...
