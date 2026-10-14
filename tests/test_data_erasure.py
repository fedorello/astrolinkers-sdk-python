"""Chart deletion, full data erasure and the plan-feature error — sync + async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AsyncAstrolinkers,
    ErasureReport,
    NotFoundError,
    PermissionDeniedError,
    PlanFeatureUnavailableError,
)

REPORT = {
    "tenant_id": "t-1",
    "charts_deleted": 2,
    "rows_deleted": 5,
    "rows_by_store": {"charts": 2, "reports": 3},
    "report_files_deleted": 1,
    "cache_entries_deleted": 2,
}


def test_sync_delete_chart_sends_delete(
    sync_client: Astrolinkers, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.delete("/v1/charts/c-1").mock(return_value=httpx.Response(204))

    sync_client.charts.delete("c-1")

    assert route.called


def test_deleting_an_unknown_chart_raises_not_found(
    sync_client: Astrolinkers, respx_mock: respx.MockRouter
) -> None:
    respx_mock.delete("/v1/charts/nope").mock(
        return_value=httpx.Response(404, json={"error": {"code": "http_error", "message": "x"}})
    )

    with pytest.raises(NotFoundError):
        sync_client.charts.delete("nope")


def test_sync_erase_all_sends_the_confirmation_phrase(
    sync_client: Astrolinkers, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.delete("/v1/tenant/data").mock(return_value=httpx.Response(200, json=REPORT))

    report = sync_client.data.erase_all()

    assert isinstance(report, ErasureReport)
    assert report.charts_deleted == 2
    assert json.loads(route.calls.last.request.content) == {"confirm": "DELETE ALL DATA"}


@pytest.mark.asyncio
async def test_async_delete_and_erase(
    async_client: AsyncAstrolinkers, respx_mock: respx.MockRouter
) -> None:
    respx_mock.delete("/v1/charts/c-1").mock(return_value=httpx.Response(204))
    respx_mock.delete("/v1/tenant/data").mock(return_value=httpx.Response(200, json=REPORT))

    await async_client.charts.delete("c-1")

    assert (await async_client.data.erase_all()).rows_deleted == 5


def test_an_llm_endpoint_on_free_raises_plan_feature_unavailable(
    sync_client: Astrolinkers, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("/v1/charts/c-1").mock(
        return_value=httpx.Response(
            403,
            json={
                "error": {
                    "code": "plan_feature_unavailable",
                    "message": "not in plan",
                    "details": {"plan": "free", "feature": "llm"},
                }
            },
        )
    )

    with pytest.raises(PlanFeatureUnavailableError) as exc:
        sync_client.charts.retrieve("c-1")

    assert isinstance(exc.value, PermissionDeniedError)
    assert exc.value.details["plan"] == "free"
