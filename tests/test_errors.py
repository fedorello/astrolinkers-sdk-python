"""Error-mapping behaviour of the transport layer.

These tests exercise :func:`_parse_error_envelope` indirectly by
hitting the public ``request`` method with crafted ``respx`` routes
so the public exception hierarchy stays the contract.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AuthenticationError,
    BudgetExceededError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ServerError,
)


def _envelope(
    code: str,
    message: str = "x",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inner: dict[str, Any] = {
        "code": code,
        "message": message,
        "message_key": f"errors.common.{code}",
    }
    if details is not None:
        inner["details"] = details
    return {"error": inner}


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (401, "unauthorized", AuthenticationError),
        (403, "forbidden", PermissionDeniedError),
        (404, "chart_not_found", NotFoundError),
        (422, "invalid_request", InvalidRequestError),
        (500, "internal_error", ServerError),
        (502, "bad_gateway", ServerError),
    ],
)
def test_status_maps_to_typed_exception(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
    status: int,
    code: str,
    expected: type[Exception],
) -> None:
    respx_mock.get("/v1/charts/x").mock(
        return_value=httpx.Response(status, json=_envelope(code)),
    )
    with pytest.raises(expected) as exc_info:
        sync_client.charts.retrieve("x")
    assert getattr(exc_info.value, "status_code", None) == status
    assert getattr(exc_info.value, "code", None) == code


def test_rate_limited_reads_retry_after_header(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/x").mock(
        return_value=httpx.Response(
            429,
            json=_envelope("llm_tier_rate_limited"),
            headers={"Retry-After": "12"},
        ),
    )
    with pytest.raises(RateLimitedError) as exc_info:
        sync_client.charts.retrieve("x")
    assert exc_info.value.retry_after_seconds == 12.0


def test_rate_limited_falls_back_to_body_when_header_missing(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/x").mock(
        return_value=httpx.Response(
            429,
            json=_envelope(
                "llm_tier_rate_limited",
                details={"retry_after_seconds": 7},
            ),
        ),
    )
    with pytest.raises(RateLimitedError) as exc_info:
        sync_client.charts.retrieve("x")
    assert exc_info.value.retry_after_seconds == 7.0


def test_budget_exceeded_carries_cap_and_spent(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/x").mock(
        return_value=httpx.Response(
            429,
            json=_envelope(
                "llm_budget_exceeded",
                details={"cap_usd": 5.00, "spent_usd": 5.43},
            ),
        ),
    )
    with pytest.raises(BudgetExceededError) as exc_info:
        sync_client.charts.retrieve("x")
    assert exc_info.value.cap_usd == 5.00
    assert exc_info.value.spent_usd == 5.43


def test_unknown_4xx_falls_through_to_invalid_request(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("/v1/charts/x").mock(
        return_value=httpx.Response(418, json=_envelope("im_a_teapot")),
    )
    with pytest.raises(InvalidRequestError):
        sync_client.charts.retrieve("x")
