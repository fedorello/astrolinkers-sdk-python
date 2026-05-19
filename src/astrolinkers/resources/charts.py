"""Charts resource — ``POST /v1/charts`` and ``GET /v1/charts/{id}``."""

from __future__ import annotations

from datetime import datetime

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.charts import Chart
from astrolinkers.types.enums import AstrologySystem, AyanamshaType, HouseSystem


def _build_payload(
    *,
    moment: datetime,
    latitude: float,
    longitude: float,
    system: AstrologySystem | str,
    house_system: HouseSystem | str,
    ayanamsha: AyanamshaType | str | None,
) -> dict[str, object]:
    """Render the request body the API expects.

    Kept as a free function so the async and sync resource classes
    share one source of truth without inheritance. Each enum-typed
    field accepts a raw ``str`` too — the server documents the
    allowed values as ``Literal[...]`` and may add new ones before
    the SDK does, so the call site should not be forced to upgrade
    in lockstep.
    """
    birth: dict[str, object] = {
        "moment": moment.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
    }

    payload: dict[str, object] = {
        "birth": birth,
        "system": system.value if isinstance(system, AstrologySystem) else system,
        "house_system": (
            house_system.value if isinstance(house_system, HouseSystem) else house_system
        ),
    }
    if ayanamsha is not None:
        payload["ayanamsha"] = (
            ayanamsha.value if isinstance(ayanamsha, AyanamshaType) else ayanamsha
        )
    return payload


class AsyncCharts:
    """Async access to chart endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        moment: datetime,
        latitude: float,
        longitude: float,
        system: AstrologySystem | str = AstrologySystem.VEDIC,
        house_system: HouseSystem | str = HouseSystem.PLACIDUS,
        ayanamsha: AyanamshaType | str | None = AyanamshaType.LAHIRI,
    ) -> Chart:
        """Compute and persist a new natal chart.

        Args:
            moment: Birth instant as an aware UTC datetime.
            latitude: Birth latitude in degrees (-90 to 90).
            longitude: Birth longitude in degrees (-180 to 180).
            system: Tropical (western) or sidereal (vedic) zodiac.
            house_system: House-division convention.
            ayanamsha: Sidereal offset; ignored for the western system.

        Returns:
            The newly created :class:`Chart`.
        """
        payload = _build_payload(
            moment=moment,
            latitude=latitude,
            longitude=longitude,
            system=system,
            house_system=house_system,
            ayanamsha=ayanamsha,
        )
        data = await self._transport.request("POST", "/v1/charts", json=payload)
        return Chart.model_validate(data)

    async def retrieve(self, chart_id: str) -> Chart:
        """Fetch a previously-created chart by id."""
        data = await self._transport.request("GET", f"/v1/charts/{chart_id}")
        return Chart.model_validate(data)


class SyncCharts:
    """Sync mirror of :class:`AsyncCharts`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        moment: datetime,
        latitude: float,
        longitude: float,
        system: AstrologySystem | str = AstrologySystem.VEDIC,
        house_system: HouseSystem | str = HouseSystem.PLACIDUS,
        ayanamsha: AyanamshaType | str | None = AyanamshaType.LAHIRI,
    ) -> Chart:
        """Compute and persist a new natal chart. See :meth:`AsyncCharts.create`."""
        payload = _build_payload(
            moment=moment,
            latitude=latitude,
            longitude=longitude,
            system=system,
            house_system=house_system,
            ayanamsha=ayanamsha,
        )
        data = self._transport.request("POST", "/v1/charts", json=payload)
        return Chart.model_validate(data)

    def retrieve(self, chart_id: str) -> Chart:
        """Fetch a previously-created chart by id."""
        data = self._transport.request("GET", f"/v1/charts/{chart_id}")
        return Chart.model_validate(data)
