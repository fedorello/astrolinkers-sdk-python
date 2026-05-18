"""Liveness / readiness / version pings.

Bypasses the API base path — these endpoints are mounted at the root
and do not require authentication. They use the same transport so
the SDK's retry / timeout / TLS settings still apply.
"""

from __future__ import annotations

from typing import Any

from astrolinkers._transport import AsyncTransport, SyncTransport


def _ensure_dict(value: Any) -> dict[str, Any]:
    """Runtime guard — the transport returns the raw decoded JSON.

    Health endpoints contract to return a JSON object; this helper
    converts a contract violation into a loud :class:`TypeError`
    rather than letting an unexpected shape (e.g. a CDN error page
    that snuck through) propagate as ``dict[str, Any]``.
    """
    if not isinstance(value, dict):
        raise TypeError(
            f"Expected JSON object from health endpoint, got {type(value).__name__}",
        )
    return value


class AsyncHealth:
    """Async health resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def healthz(self) -> dict[str, Any]:
        """Server-side liveness check. Always ``{"status": "ok"}``."""
        return _ensure_dict(await self._transport.request("GET", "/healthz"))

    async def readyz(self) -> dict[str, Any]:
        """Deeper readiness probe — DB + cache + LLM provider reachability."""
        return _ensure_dict(await self._transport.request("GET", "/readyz"))

    async def version(self) -> dict[str, Any]:
        """Build metadata: git SHA, version tag, deploy time."""
        return _ensure_dict(await self._transport.request("GET", "/version"))


class SyncHealth:
    """Sync mirror of :class:`AsyncHealth`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def healthz(self) -> dict[str, Any]:
        """Server-side liveness check."""
        return _ensure_dict(self._transport.request("GET", "/healthz"))

    def readyz(self) -> dict[str, Any]:
        """Deeper readiness probe — DB + cache + LLM provider reachability."""
        return _ensure_dict(self._transport.request("GET", "/readyz"))

    def version(self) -> dict[str, Any]:
        """Build metadata: git SHA, version tag, deploy time."""
        return _ensure_dict(self._transport.request("GET", "/version"))
