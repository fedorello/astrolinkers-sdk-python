"""Compatibility resource — synastry + ashtakoota between two charts."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.compatibility import CompatibilityAxis, CompatibilityReport


def _create_body(
    *,
    chart_a_id: str,
    chart_b_id: str,
    axis: CompatibilityAxis,
    include_ashtakoota: bool,
    include_synastry: bool,
) -> dict[str, object]:
    return {
        "chart_a_id": chart_a_id,
        "chart_b_id": chart_b_id,
        "axis": axis,
        "include_ashtakoota": include_ashtakoota,
        "include_synastry": include_synastry,
    }


class AsyncCompatibility:
    """Async compatibility resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        chart_a_id: str,
        chart_b_id: str,
        axis: CompatibilityAxis = "talent",
        include_ashtakoota: bool = True,
        include_synastry: bool = True,
    ) -> CompatibilityReport:
        """Compute a compatibility report between two charts."""
        data = await self._transport.request(
            "POST",
            "/v1/compatibility",
            json=_create_body(
                chart_a_id=chart_a_id,
                chart_b_id=chart_b_id,
                axis=axis,
                include_ashtakoota=include_ashtakoota,
                include_synastry=include_synastry,
            ),
        )
        return CompatibilityReport.model_validate(data)

    async def retrieve(self, report_id: str) -> CompatibilityReport:
        """Fetch a stored compatibility report."""
        data = await self._transport.request(
            "GET",
            f"/v1/compatibility/{report_id}",
        )
        return CompatibilityReport.model_validate(data)


class SyncCompatibility:
    """Sync mirror of :class:`AsyncCompatibility`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        chart_a_id: str,
        chart_b_id: str,
        axis: CompatibilityAxis = "talent",
        include_ashtakoota: bool = True,
        include_synastry: bool = True,
    ) -> CompatibilityReport:
        """Compute a compatibility report between two charts."""
        data = self._transport.request(
            "POST",
            "/v1/compatibility",
            json=_create_body(
                chart_a_id=chart_a_id,
                chart_b_id=chart_b_id,
                axis=axis,
                include_ashtakoota=include_ashtakoota,
                include_synastry=include_synastry,
            ),
        )
        return CompatibilityReport.model_validate(data)

    def retrieve(self, report_id: str) -> CompatibilityReport:
        """Fetch a stored compatibility report."""
        data = self._transport.request(
            "GET",
            f"/v1/compatibility/{report_id}",
        )
        return CompatibilityReport.model_validate(data)
