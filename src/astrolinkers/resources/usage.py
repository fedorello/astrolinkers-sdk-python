"""Usage resource — hourly API-call buckets per key / per tenant.

Distinct from :meth:`AsyncLLM.usage_summary` which aggregates LLM
spend; this resource counts raw API hits.
"""

from __future__ import annotations

from datetime import datetime

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.usage_buckets import HourlyUsage


def _params(
    since: datetime | None,
    until: datetime | None,
) -> dict[str, object]:
    return {
        "since": since.isoformat() if since else None,
        "until": until.isoformat() if until else None,
    }


class AsyncUsage:
    """Async usage resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def api_key(
        self,
        key_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> HourlyUsage:
        """Hourly usage for one API key."""
        data = await self._transport.request(
            "GET",
            f"/v1/api-keys/{key_id}/usage",
            params=_params(since, until),
        )
        return HourlyUsage.model_validate(data)

    async def tenant(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> HourlyUsage:
        """Tenant-wide hourly usage."""
        data = await self._transport.request(
            "GET",
            "/v1/tenant/usage",
            params=_params(since, until),
        )
        return HourlyUsage.model_validate(data)


class SyncUsage:
    """Sync mirror of :class:`AsyncUsage`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def api_key(
        self,
        key_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> HourlyUsage:
        """Hourly usage for one API key."""
        data = self._transport.request(
            "GET",
            f"/v1/api-keys/{key_id}/usage",
            params=_params(since, until),
        )
        return HourlyUsage.model_validate(data)

    def tenant(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> HourlyUsage:
        """Tenant-wide hourly usage."""
        data = self._transport.request(
            "GET",
            "/v1/tenant/usage",
            params=_params(since, until),
        )
        return HourlyUsage.model_validate(data)
