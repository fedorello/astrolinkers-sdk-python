"""Data resource — erase everything the account has stored (``DELETE /v1/tenant/data``)."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.data import ErasureReport

# The phrase the API requires so a full erasure cannot happen by accident.
ERASE_ALL_CONFIRMATION = "DELETE ALL DATA"


class AsyncData:
    """Async access to data erasure."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def erase_all(self) -> ErasureReport:
        """Delete every chart of the account and everything derived from them.

        The account, API keys and usage history stay. Cannot be undone.
        """
        data = await self._transport.request(
            "DELETE",
            "/v1/tenant/data",
            json={"confirm": ERASE_ALL_CONFIRMATION},
        )
        return ErasureReport.model_validate(data)


class SyncData:
    """Sync mirror of :class:`AsyncData`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def erase_all(self) -> ErasureReport:
        """Delete every chart of the account and everything derived from them."""
        data = self._transport.request(
            "DELETE",
            "/v1/tenant/data",
            json={"confirm": ERASE_ALL_CONFIRMATION},
        )
        return ErasureReport.model_validate(data)
