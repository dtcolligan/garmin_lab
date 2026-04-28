"""W-X: Probe protocol for `hai doctor --deep` (Codex F-DEMO-01).

`hai doctor` reports `auth_intervals_icu: ok` whenever credentials
are present in the keyring, but says nothing about whether the
remote API still accepts them. The 2026-04-28 demo run exposed the
gap: the credential surface was green while a live wellness fetch
returned HTTP 403.

`hai doctor --deep` adds a probe call. In real mode the probe hits
the remote API (LiveProbe). In demo mode (a valid marker is active)
the probe routes to a fixture stub (FixtureProbe) — preserves the
demo moment of "doctor caught broken auth" without any network
call (per maintainer answer Q-3 on plan-audit round 2).

Contract:

- Probe.probe_intervals_icu(credentials) -> ProbeResult
- Probe.probe_garmin(credentials)        -> ProbeResult

ProbeResult fields: ok (bool), source ("live" | "fixture"),
http_status (Optional[int]), error_message (Optional[str]).

The doctor check helpers return a dict that includes a `probe`
sub-dict when `--deep` is set, with shape:
    {"ok": bool, "source": "live"|"fixture", "http_status": int|None,
     "error_message": str|None}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a single deep-probe call against a credential surface.

    ``source`` is "live" when the probe actually hit the network and
    "fixture" when a stubbed response was returned (demo mode).
    Tests assert on this field to enforce the no-network invariant
    in demo mode.
    """

    ok: bool
    source: str  # "live" | "fixture"
    http_status: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "http_status": self.http_status,
            "error_message": self.error_message,
        }


class Probe(Protocol):
    """Probe surface for the deep-doctor checks."""

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult: ...
    def probe_garmin(self, credentials: Any) -> ProbeResult: ...


class LiveProbe:
    """Real-network probe used in non-demo (real) mode.

    Reuses the existing intervals.icu adapter for a minimum-scope
    fetch. v0.1.11 W-X scope: probe intervals.icu only; Garmin
    surface gets a placeholder fixture-OK because the Garmin live
    path is rate-limited per AGENTS.md and not the recommended
    primary source.
    """

    def __init__(self, *, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult:
        from datetime import date, timedelta
        from health_agent_infra.core.pull.intervals_icu import (
            HttpIntervalsIcuClient,
            IntervalsIcuError,
        )

        client = HttpIntervalsIcuClient(
            credentials=credentials,
            timeout_seconds=self.timeout_seconds,
        )
        # Minimal-scope query: a single recent date. Fail fast.
        today = date.today()
        try:
            client.fetch_wellness_range(today - timedelta(days=1), today)
        except IntervalsIcuError as exc:
            msg = str(exc)
            # Try to pull HTTP status if the message contains it.
            http_status: Optional[int] = None
            for token in msg.split():
                if token.isdigit() and 100 <= int(token) <= 599:
                    http_status = int(token)
                    break
            return ProbeResult(
                ok=False,
                source="live",
                http_status=http_status,
                error_message=msg,
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                ok=False,
                source="live",
                error_message=f"{type(exc).__name__}: {exc}",
            )
        return ProbeResult(ok=True, source="live", http_status=200)

    def probe_garmin(self, credentials: Any) -> ProbeResult:
        # Garmin live login is rate-limited and unreliable per AGENTS.md
        # ("Garmin Connect is not the default live source"). v0.1.11
        # W-X does not introduce a new Garmin live probe. A future
        # workstream may add one; for now, return a "live-skipped"
        # result that surfaces honestly in the doctor row.
        return ProbeResult(
            ok=False,
            source="live",
            error_message=(
                "Garmin live probe not implemented (rate-limited per "
                "AGENTS.md; intervals.icu is the recommended live source)"
            ),
        )


class FixtureProbe:
    """Demo-mode probe — returns a fixture response without any network.

    The fixture is set per probe surface: a default 200-OK response
    when no override is supplied, or a caller-specified
    :class:`ProbeResult` when the demo persona / test wants to
    exercise a specific failure mode (e.g., a 403 to demo the
    diagnostic-trust feature).

    A hard no-network guard runs in tests via socket-monkeypatch;
    this class itself never opens a socket.
    """

    def __init__(
        self,
        *,
        intervals_icu_response: Optional[ProbeResult] = None,
        garmin_response: Optional[ProbeResult] = None,
    ) -> None:
        self._intervals_icu = intervals_icu_response or ProbeResult(
            ok=True, source="fixture", http_status=200
        )
        self._garmin = garmin_response or ProbeResult(
            ok=True, source="fixture", http_status=200
        )

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult:
        return self._intervals_icu

    def probe_garmin(self, credentials: Any) -> ProbeResult:
        return self._garmin


def resolve_probe(*, demo_active: bool) -> Probe:
    """Return the probe implementation appropriate for the current mode.

    Demo mode → :class:`FixtureProbe` (default 200-OK responses).
    Real mode → :class:`LiveProbe`.

    Test-friendly override: pass an explicit ``Probe`` to
    :func:`run_deep_probes` instead of using this helper.
    """
    if demo_active:
        return FixtureProbe()
    return LiveProbe()


def run_deep_probes(
    *,
    probe: Probe,
    credential_store: Any,
) -> dict[str, ProbeResult]:
    """Run the configured probe against intervals.icu + Garmin and
    return a per-source dict of :class:`ProbeResult`.

    Skips probes when credentials are absent (the credential
    surface already returns ``warn`` in that case; the deep probe
    has nothing to probe).
    """

    out: dict[str, ProbeResult] = {}

    intervals_status = credential_store.intervals_icu_status()
    if intervals_status.get("credentials_available"):
        creds = credential_store.load_intervals_icu()
        if creds is not None:
            out["intervals_icu"] = probe.probe_intervals_icu(creds)

    garmin_status = credential_store.garmin_status()
    if garmin_status.get("credentials_available"):
        creds = credential_store.load_garmin()
        if creds is not None:
            out["garmin"] = probe.probe_garmin(creds)

    return out
