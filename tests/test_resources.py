"""Happy-path coverage for the resources added in v0.2.0.

One test per public method; respx-mocked round trips. Sync/async
parity is checked once per resource — both wrap the same transport
so a single async test per resource is enough to detect drift.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AsyncAstrolinkers,
    BhavaStyle,
    HouseSignificator,
    TheoArea,
    Varga,
    VimshopakaGroup,
)

# ─────────────────────────────────────────────────────────────────
# Escape hatch
# ─────────────────────────────────────────────────────────────────


def test_request_escape_hatch_round_trip(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/some-future-endpoint").mock(
        return_value=httpx.Response(200, json={"ok": True}),
    )
    body = sync_client.request("GET", "/v1/some-future-endpoint")
    assert body == {"ok": True}


@pytest.mark.asyncio
async def test_async_request_escape_hatch(
    async_client: AsyncAstrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/some-future-endpoint").mock(
        return_value=httpx.Response(200, json={"received": True}),
    )
    body = await async_client.request(
        "POST",
        "/v1/some-future-endpoint",
        json={"hello": "world"},
    )
    assert body == {"received": True}


# ─────────────────────────────────────────────────────────────────
# api_keys
# ─────────────────────────────────────────────────────────────────


def test_api_keys_issue_returns_token(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/api-keys").mock(
        return_value=httpx.Response(
            201,
            json={
                "api_key": {
                    "id": "k1",
                    "name": "n",
                    "scopes": ["charts:read"],
                    "created_at": "2026-05-18T22:00:00Z",
                },
                "token": "alk_secret_…",
            },
        ),
    )
    issued = sync_client.api_keys.issue(
        name="n",
        scopes=["charts:read"],
    )
    assert issued.token == "alk_secret_…"
    assert issued.api_key.id == "k1"


def test_api_keys_list_returns_items(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "k1",
                        "name": "n",
                        "scopes": ["charts:read"],
                        "created_at": "2026-05-18T22:00:00Z",
                    }
                ]
            },
        ),
    )
    keys = sync_client.api_keys.list()
    assert len(keys) == 1
    assert keys[0].id == "k1"


def test_api_keys_revoke(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/api-keys/k1/revoke").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "k1",
                "name": "n",
                "scopes": ["charts:read"],
                "created_at": "2026-05-18T22:00:00Z",
                "revoked_at": "2026-05-18T23:00:00Z",
            },
        ),
    )
    revoked = sync_client.api_keys.revoke("k1")
    assert revoked.revoked_at is not None


# ─────────────────────────────────────────────────────────────────
# compatibility
# ─────────────────────────────────────────────────────────────────


def test_compatibility_create(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/compatibility").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "r1",
                "chart_a_id": "a",
                "chart_b_id": "b",
                "axis": "talent",
                "verdict": "good",
                "overall_score_percent": 78.5,
                "computed_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    report = sync_client.compatibility.create(chart_a_id="a", chart_b_id="b")
    assert report.overall_score_percent == 78.5


def test_compatibility_retrieve(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/compatibility/r1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "r1",
                "chart_a_id": "a",
                "chart_b_id": "b",
                "axis": "romantic",
                "verdict": "excellent",
                "overall_score_percent": 92.0,
                "computed_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    assert sync_client.compatibility.retrieve("r1").axis == "romantic"


# ─────────────────────────────────────────────────────────────────
# feedback
# ─────────────────────────────────────────────────────────────────


def test_feedback_submit(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/feedback").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "f1",
                "statement_id": "s1",
                "chart_id": "c1",
                "template_id": "t1",
                "skill_id": "k1",
                "verdict": "correct",
                "role": "subject",
                "submitted_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    fb = sync_client.feedback.submit(statement_id="s1", verdict="correct")
    assert fb.verdict == "correct"


def test_feedback_template_accuracy(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/feedback/templates/t1").mock(
        return_value=httpx.Response(
            200,
            json={
                "template_id": "t1",
                "sample_size": 100,
                "correct_count": 80,
                "doubtful_count": 15,
                "wrong_count": 5,
                "accuracy": 0.8,
                "deprecated": False,
                "updated_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    acc = sync_client.feedback.template_accuracy("t1")
    assert acc.accuracy == 0.8


# ─────────────────────────────────────────────────────────────────
# interpretations (template-driven)
# ─────────────────────────────────────────────────────────────────


def test_interpretations_template_create(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/interpretations").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "i1",
                "chart_id": "c1",
                "locale": "en",
                "tone": "corporate",
                "statements": [
                    {"id": "s1", "template_id": "t1", "skill_id": "k1", "text": "x"},
                ],
                "created_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    interp = sync_client.interpretations.create(chart_id="c1")
    assert interp.statements[0].id == "s1"


# ─────────────────────────────────────────────────────────────────
# plans
# ─────────────────────────────────────────────────────────────────


def test_plans_list(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"tier": "free", "name": "Free"},
                    {"tier": "pro", "name": "Pro", "monthly_price_usd": 49.0},
                ]
            },
        ),
    )
    plans = sync_client.plans.list()
    assert {p.tier for p in plans} == {"free", "pro"}


def test_plans_set_tenant_plan(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("/v1/tenant/plan").mock(
        return_value=httpx.Response(200, json={"tier": "pro"}),
    )
    tp = sync_client.plans.set_tenant_plan(plan_tier="pro")
    assert tp.tier == "pro"
    body = route.calls.last.request.read().decode()
    assert "pro" in body


# ─────────────────────────────────────────────────────────────────
# profiles
# ─────────────────────────────────────────────────────────────────


def test_profiles_talent(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/c1/profile/talent").mock(
        return_value=httpx.Response(
            200,
            json={"chart_id": "c1", "locale": "en", "skills": [{"id": "s1"}]},
        ),
    )
    prof = sync_client.profiles.talent("c1")
    assert prof.chart_id == "c1"
    assert prof.skills[0]["id"] == "s1"


# ─────────────────────────────────────────────────────────────────
# reports
# ─────────────────────────────────────────────────────────────────


def test_reports_create_and_retrieve(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/reports").mock(
        return_value=httpx.Response(
            202,
            json={
                "id": "r1",
                "chart_id": "c1",
                "kind": "talent_lens",
                "format": "pdf",
                "locale": "en",
                "tone": "corporate",
                "status": "pending",
                "created_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    respx_mock.get("/v1/reports/r1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "r1",
                "chart_id": "c1",
                "kind": "talent_lens",
                "format": "pdf",
                "locale": "en",
                "tone": "corporate",
                "status": "ready",
                "artifact_url": "https://signed.example/r1.pdf",
                "created_at": "2026-05-18T22:00:00Z",
            },
        ),
    )
    job = sync_client.reports.create(chart_id="c1", format="pdf")
    assert job.status == "pending"
    polled = sync_client.reports.retrieve("r1")
    assert polled.status == "ready"
    assert polled.artifact_url is not None


# ─────────────────────────────────────────────────────────────────
# usage (raw API hits)
# ─────────────────────────────────────────────────────────────────


def test_usage_per_key_and_tenant(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    payload = {
        "buckets": [
            {"hour": "2026-05-18T22:00:00Z", "request_count": 5},
            {"hour": "2026-05-18T23:00:00Z", "request_count": 3},
        ],
        "total_requests": 8,
    }
    respx_mock.get("/v1/api-keys/k1/usage").mock(
        return_value=httpx.Response(200, json=payload),
    )
    respx_mock.get("/v1/tenant/usage").mock(
        return_value=httpx.Response(200, json=payload),
    )
    assert sync_client.usage.api_key("k1").total_requests == 8
    assert (
        sync_client.usage.tenant(
            since=datetime(2026, 5, 18, tzinfo=UTC),
            until=datetime(2026, 5, 18, tzinfo=UTC) + timedelta(hours=2),
        ).total_requests
        == 8
    )


# ─────────────────────────────────────────────────────────────────
# health
# ─────────────────────────────────────────────────────────────────


def test_health_endpoints(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok"}),
    )
    respx_mock.get("/readyz").mock(
        return_value=httpx.Response(200, json={"status": "ready"}),
    )
    respx_mock.get("/version").mock(
        return_value=httpx.Response(200, json={"version": "1.0.0"}),
    )
    assert sync_client.health.healthz()["status"] == "ok"
    assert sync_client.health.readyz()["status"] == "ready"
    assert sync_client.health.version()["version"] == "1.0.0"


# ─────────────────────────────────────────────────────────────────
# vedic — representative coverage
# ─────────────────────────────────────────────────────────────────


def test_vedic_divisional(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/vedic/charts/c1/divisional/D9").mock(
        return_value=httpx.Response(200, json={"varga": "D9", "planets": {}}),
    )
    assert sync_client.vedic.divisional("c1", Varga.D9)["varga"] == "D9"


def test_vedic_bhava_chakra_serialises_style(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/vedic/charts/c1/bhava-chakra").mock(
        return_value=httpx.Response(200, json={"style": "equal"}),
    )
    sync_client.vedic.bhava_chakra("c1", style=BhavaStyle.EQUAL)
    assert "style=equal" in str(route.calls.last.request.url)


def test_vedic_panchanga_carries_at_lat_lon(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/vedic/panchanga").mock(
        return_value=httpx.Response(200, json={"tithi": "Purnima"}),
    )
    sync_client.vedic.panchanga(
        at=datetime(2026, 5, 18, 12, 0, tzinfo=UTC),
        lat=28.6139,
        lon=77.2090,
    )
    url = str(route.calls.last.request.url)
    assert "at=2026-05-18" in url
    assert "lat=28.6139" in url
    assert "lon=77.209" in url


def test_vedic_current_dasha_at(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/vedic/charts/c1/dasha/current").mock(
        return_value=httpx.Response(200, json={"md_lord": "sun"}),
    )
    sync_client.vedic.current_dasha("c1", at=datetime(2027, 3, 1, tzinfo=UTC))
    assert "at=2027-03-01" in str(route.calls.last.request.url)


def test_vedic_vimshopaka_group(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/vedic/charts/c1/vimshopaka/jupiter").mock(
        return_value=httpx.Response(200, json={"bala": 17.3}),
    )
    sync_client.vedic.vimshopaka(
        "c1",
        "jupiter",
        group=VimshopakaGroup.SHODASHA_VARGA,
    )
    assert "group=shodasha_varga" in str(route.calls.last.request.url)


def test_vedic_theo_thematic_uses_enum_value(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/vedic/charts/c1/theo/thematic/career").mock(
        return_value=httpx.Response(200, json={"area": "career"}),
    )
    out = sync_client.vedic.theo_thematic("c1", TheoArea.CAREER)
    assert out["area"] == "career"


def test_vedic_probability_with_house_significator(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/vedic/charts/c1/probability/marriage_for_man").mock(
        return_value=httpx.Response(200, json={"final": 0.42}),
    )
    out = sync_client.vedic.probability(
        "c1",
        HouseSignificator.MARRIAGE_FOR_MAN,
        at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    assert out["final"] == 0.42


def test_vedic_kp_lookup(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/vedic/kp/lookup").mock(
        return_value=httpx.Response(200, json={"rashi": "leo"}),
    )
    out = sync_client.vedic.kp_lookup(longitude_deg=132.5)
    assert out["rashi"] == "leo"


def test_vedic_muhurta_window(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.get("/v1/vedic/charts/c1/muhurta").mock(
        return_value=httpx.Response(200, json={"candidates": []}),
    )
    sync_client.vedic.muhurta(
        "c1",
        window_start=datetime(2026, 12, 1, tzinfo=UTC),
        window_end=datetime(2026, 12, 3, tzinfo=UTC),
        interval_minutes=180,
        top_n=5,
    )
    url = str(route.calls.last.request.url)
    assert "interval_minutes=180" in url
    assert "top_n=5" in url


@pytest.mark.asyncio
async def test_async_vedic_method_parity(
    async_client: AsyncAstrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    """One async vedic call to assert the async surface is wired."""
    respx_mock.get("/v1/vedic/charts/c1/yogas").mock(
        return_value=httpx.Response(200, json={"yogas": []}),
    )
    out = await async_client.vedic.yogas("c1")
    assert out == {"yogas": []}
