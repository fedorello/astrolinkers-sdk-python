"""LLM resource — non-streaming endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AsyncAstrolinkers,
    InterpretationTier,
    Language,
    LLMInterpretation,
)

INTERP_PAYLOAD = {
    "interpretation_type": "theme",
    "language": "en",
    "tier": "standard",
    "content": "Your career theme…",
    "engine_context": {"theme": "career"},
    "input_tokens": 100,
    "output_tokens": 250,
    "latency_ms": 4200,
    "cost_usd": 0.0021,
    "interpretation_id": "019e3d4f-…",
    "cached": False,
}


def test_theme_sends_query_params(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/llm/theme/career").mock(
        return_value=httpx.Response(200, json=INTERP_PAYLOAD),
    )
    result = sync_client.llm.theme(
        chart_id="c1",
        theme="career",
        language=Language.EN,
        tier=InterpretationTier.STANDARD,
    )
    assert isinstance(result, LLMInterpretation)
    assert result.content.startswith("Your career theme")
    req = route.calls.last.request
    assert "chart_id=c1" in str(req.url)
    assert "language=en" in str(req.url)
    assert "tier=standard" in str(req.url)


def test_fresh_query_param_serialised_when_true(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/llm/theme/career").mock(
        return_value=httpx.Response(200, json=INTERP_PAYLOAD),
    )
    sync_client.llm.theme(chart_id="c1", theme="career", fresh=True)
    assert "fresh=True" in str(route.calls.last.request.url) or "fresh=true" in str(
        route.calls.last.request.url
    )


def test_fresh_omitted_when_false(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/llm/theme/career").mock(
        return_value=httpx.Response(200, json=INTERP_PAYLOAD),
    )
    sync_client.llm.theme(chart_id="c1", theme="career", fresh=False)
    assert "fresh" not in str(route.calls.last.request.url)


def test_chart_reading_uses_dedicated_path(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    payload = INTERP_PAYLOAD | {"interpretation_type": "chart_reading"}
    respx_mock.post("/v1/llm/chart-reading").mock(
        return_value=httpx.Response(200, json=payload),
    )
    result = sync_client.llm.chart_reading(chart_id="c1", tier=InterpretationTier.PREMIUM)
    assert result.interpretation_type.value == "chart_reading"


def test_dasha_forecast_sends_at(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    payload = INTERP_PAYLOAD | {"interpretation_type": "dasha_forecast"}
    route = respx_mock.post("/v1/llm/dasha-forecast").mock(
        return_value=httpx.Response(200, json=payload),
    )
    sync_client.llm.dasha_forecast(
        chart_id="c1",
        at=datetime(2027, 3, 1, 12, 0, tzinfo=UTC),
    )
    assert "at=2027-03-01" in str(route.calls.last.request.url)


def test_muhurta_reasoning_sends_window(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    payload = INTERP_PAYLOAD | {"interpretation_type": "muhurta"}
    route = respx_mock.post("/v1/llm/muhurta-reasoning").mock(
        return_value=httpx.Response(200, json=payload),
    )
    sync_client.llm.muhurta_reasoning(
        chart_id="c1",
        window_start=datetime(2026, 12, 1, tzinfo=UTC),
        window_end=datetime(2026, 12, 5, tzinfo=UTC),
        interval_minutes=240,
        top_n=3,
    )
    url = str(route.calls.last.request.url)
    assert "interval_minutes=240" in url
    assert "top_n=3" in url


@pytest.mark.asyncio
async def test_async_theme_round_trip(
    async_client: AsyncAstrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/llm/theme/career").mock(
        return_value=httpx.Response(200, json=INTERP_PAYLOAD),
    )
    result = await async_client.llm.theme(chart_id="c1", theme="career")
    assert result.cached is False
