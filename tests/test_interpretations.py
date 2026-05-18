"""Stored interpretations + usage-summary resources."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import respx

from astrolinkers import (
    Astrolinkers,
    InterpretationTier,
    Language,
    UsageGroupBy,
)

STORED_PAYLOAD = {
    "id": "019e3d4f-…",
    "chart_id": "c1",
    "interpretation_type": "theme",
    "theme": "career",
    "language": "en",
    "tier": "basic",
    "content": "x",
    "engine_context": {},
    "request_params": {"at": None},
    "input_tokens": 100,
    "output_tokens": 250,
    "latency_ms": 4200,
    "cost_usd": 0.0021,
    "created_at": "2026-05-18T22:30:00Z",
}


def test_list_serialises_all_filters(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/llm/interpretations").mock(
        return_value=httpx.Response(
            200,
            json={"items": [STORED_PAYLOAD], "total": 1, "limit": 50, "offset": 0},
        ),
    )
    page = sync_client.interpretations.list(
        chart_id="c1",
        interpretation_type="theme",
        language=Language.EN,
        tier=InterpretationTier.BASIC,
        limit=10,
        offset=5,
    )
    assert page.total == 1
    url = str(route.calls.last.request.url)
    assert "chart_id=c1" in url
    assert "interpretation_type=theme" in url
    assert "language=en" in url
    assert "tier=basic" in url
    assert "limit=10" in url
    assert "offset=5" in url


def test_retrieve_one_returns_typed_model(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/llm/interpretations/019e3d4f-").mock(
        return_value=httpx.Response(200, json=STORED_PAYLOAD),
    )
    row = sync_client.interpretations.retrieve("019e3d4f-")
    assert row.interpretation_type.value == "theme"
    assert row.theme == "career"
    assert row.cost_usd == 0.0021


def test_usage_summary_serialises_from_and_group_by(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    payload = {
        "from_": "2026-05-18T00:00:00Z",
        "to": "2026-05-19T00:00:00Z",
        "group_by": "tier",
        "total": {
            "label": None,
            "call_count": 3,
            "input_tokens": 600,
            "output_tokens": 900,
            "cost_usd": 0.005,
        },
        "breakdown": [
            {
                "label": "basic",
                "call_count": 2,
                "input_tokens": 400,
                "output_tokens": 500,
                "cost_usd": 0.001,
            },
            {
                "label": "premium",
                "call_count": 1,
                "input_tokens": 200,
                "output_tokens": 400,
                "cost_usd": 0.004,
            },
        ],
    }
    route = respx_mock.get("/v1/llm/usage-summary").mock(
        return_value=httpx.Response(200, json=payload),
    )
    summary = sync_client.interpretations.usage_summary(
        from_=datetime(2026, 5, 18, tzinfo=UTC),
        to=datetime(2026, 5, 19, tzinfo=UTC),
        group_by=UsageGroupBy.TIER,
    )
    assert summary.total.call_count == 3
    assert {b.label for b in summary.breakdown} == {"basic", "premium"}
    url = str(route.calls.last.request.url)
    assert "from=2026-05-18" in url
    assert "to=2026-05-19" in url
    assert "group_by=tier" in url
