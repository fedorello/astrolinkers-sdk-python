"""Shared fixtures for the SDK test suite.

Two style fixtures:

* ``async_client`` — :class:`AsyncAstrolinkers` wired into a respx-
  controlled HTTP transport. Every test that needs HTTP I/O takes
  this fixture.
* ``sync_client``  — :class:`Astrolinkers` (sync) variant for the
  sibling tests.

respx is configured so any unmocked request raises an explicit
``AllMockedAssertionError`` instead of silently hitting the network.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from astrolinkers import Astrolinkers, AsyncAstrolinkers

BASE_URL = "https://api.test.astrolinkers.com"
TEST_API_KEY = "alk_test_token"


@pytest.fixture
def respx_mock() -> Iterator[respx.MockRouter]:
    """Provide a respx router scoped to the API base url.

    ``assert_all_called=False`` because individual tests stub the
    minimum set of routes they need; the router still rejects
    unmocked calls, which is the strict behaviour we want.
    """
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
async def async_client(
    respx_mock: respx.MockRouter,
) -> AsyncIterator[AsyncAstrolinkers]:
    """Async client whose HTTP layer goes through respx_mock."""
    transport = httpx.AsyncHTTPTransport()
    http_client = httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        transport=transport,
    )
    client = AsyncAstrolinkers(
        api_key=TEST_API_KEY,
        base_url=BASE_URL,
        max_retries=0,
        http_client=http_client,
    )
    try:
        yield client
    finally:
        await client.aclose()
    # respx is consumed via the fixture's context manager; reference
    # it so the linter knows it is intentionally injected.
    _ = respx_mock


@pytest.fixture
def sync_client(
    respx_mock: respx.MockRouter,
) -> Iterator[Astrolinkers]:
    """Sync client wired into respx_mock."""
    http_client = httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )
    client = Astrolinkers(
        api_key=TEST_API_KEY,
        base_url=BASE_URL,
        max_retries=0,
        http_client=http_client,
    )
    try:
        yield client
    finally:
        client.close()
    _ = respx_mock
