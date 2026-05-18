"""Charts resource — happy paths in sync + async."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AstrologySystem,
    AsyncAstrolinkers,
    AyanamshaType,
    Chart,
    HouseSystem,
)

CHART_PAYLOAD = {
    "id": "019e3cdd-14d9-7960-924f-26578bb111f5",
    "system": "vedic",
    "ayanamsha": "lahiri",
    "house_system": "whole_sign",
    "computed_at": "2026-05-18T22:00:00Z",
    "birth": {
        "moment": "1990-04-15T02:00:00Z",
        "latitude": 28.6139,
        "longitude": 77.209,
        "timezone": "Asia/Kolkata",
    },
    "planets": [
        {
            "planet": "sun",
            "longitude": 24.5,
            "speed_per_day": 0.985,
            "is_retrograde": False,
            "nakshatra": "Bharani",
            "pada": 3,
        },
    ],
    "houses": [{"house_number": 1, "longitude": 5.0}],
}


def test_sync_create_sends_birth_block_and_parses_chart(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/charts").mock(
        return_value=httpx.Response(201, json=CHART_PAYLOAD),
    )
    chart = sync_client.charts.create(
        moment=datetime(1990, 4, 15, 2, 0, tzinfo=UTC),
        latitude=28.6139,
        longitude=77.2090,
        timezone="Asia/Kolkata",
        system=AstrologySystem.VEDIC,
        house_system=HouseSystem.WHOLE_SIGN,
        ayanamsha=AyanamshaType.LAHIRI,
    )
    assert isinstance(chart, Chart)
    assert chart.id == CHART_PAYLOAD["id"]
    # The request body matched our expectation.
    body = route.calls.last.request.read().decode()
    assert "Asia/Kolkata" in body
    assert "lahiri" in body
    assert "vedic" in body
    assert "1990-04-15T02:00:00" in body


def test_sync_retrieve_uses_correct_path(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/abc").mock(
        return_value=httpx.Response(200, json=CHART_PAYLOAD),
    )
    chart = sync_client.charts.retrieve("abc")
    assert chart.id == CHART_PAYLOAD["id"]


@pytest.mark.asyncio
async def test_async_create_sends_birth_block(
    async_client: AsyncAstrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/charts").mock(
        return_value=httpx.Response(201, json=CHART_PAYLOAD),
    )
    chart = await async_client.charts.create(
        moment=datetime(1990, 4, 15, 2, 0, tzinfo=UTC),
        latitude=28.6139,
        longitude=77.2090,
    )
    assert chart.id == CHART_PAYLOAD["id"]
    body = route.calls.last.request.read().decode()
    assert "1990-04-15" in body
