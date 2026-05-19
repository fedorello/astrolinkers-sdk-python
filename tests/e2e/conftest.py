"""Shared fixtures for the e2e smoke suite.

All tests in this directory talk to the real staging API at
``https://api.astrolinkers.com``. They are gated by
``ASTROLINKERS_E2E_TOKEN`` (typically the founder JWT) and skip
cleanly when the env var is missing.

Fixture lifecycle:

* ``founder_token``      — module-scoped; raw JWT used to bootstrap.
* ``issued_test_key``    — session-scoped; a 1-hour test API key
  issued via the SDK and revoked at teardown.
* ``sync_client`` / ``async_client`` — built against the issued test
  key so test bodies do not see admin scopes.
* ``chart_a`` / ``chart_b`` — two stable natal charts used by every
  per-chart endpoint.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio

from astrolinkers import (
    Astrolinkers,
    AstrologySystem,
    AsyncAstrolinkers,
    AyanamshaType,
    Chart,
    HouseSystem,
    IssuedApiKey,
)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Staging endpoint we exercise. Pinned here so a misconfigured
# ``ASTROLINKERS_BASE_URL`` env never accidentally hits production from
# the local machine without an explicit code change.
DEFAULT_BASE_URL = "https://api.astrolinkers.com"

# Founder JWT location — same path documented in ``~/.astrolinkers/AUTH.md``.
FOUNDER_TOKEN_PATH = Path.home() / ".astrolinkers" / "token_founder.jwt"

# Scopes for the throwaway test key. Mirrors every scope the SDK
# resources can possibly exercise. ``admin`` is deliberately omitted
# because the server forbids minting admin-scoped keys through the
# self-service endpoint.
TEST_KEY_SCOPES: list[str] = [
    "charts:read",
    "charts:write",
    "interpretations:read",
    "interpretations:write",
    "compatibility:read",
    "compatibility:write",
    "feedback:read",
    "feedback:write",
    "reports:read",
    "reports:write",
    "keys:manage",
]

# Stable chart fixtures — pinned moments so server-side determinism
# kicks in and the same divisional / dasha values come back across
# runs. Two charts so the compatibility resource can be exercised.
CHART_A_MOMENT = datetime(1990, 4, 15, 2, 0, tzinfo=UTC)
CHART_A_LAT = 28.6139
CHART_A_LON = 77.2090

CHART_B_MOMENT = datetime(1992, 7, 23, 8, 30, tzinfo=UTC)
CHART_B_LAT = 19.0760
CHART_B_LON = 72.8777


# ----------------------------------------------------------------------------
# Token + key fixtures
# ----------------------------------------------------------------------------


@pytest.fixture(scope="session")
def founder_token() -> str:
    """Return the founder JWT.

    Resolution order:

    1. ``ASTROLINKERS_E2E_TOKEN`` env var (preferred — keeps secrets
       out of the working directory).
    2. ``~/.astrolinkers/token_founder.jwt`` on disk.

    The module-level ``pytestmark`` in :mod:`tests.e2e.test_smoke`
    already skips the whole module when neither is present, so this
    fixture only runs when a token is available.
    """
    env_token = os.environ.get("ASTROLINKERS_E2E_TOKEN")
    if env_token:
        return env_token.strip()
    return FOUNDER_TOKEN_PATH.read_text().strip()


@pytest.fixture(scope="session")
def base_url() -> str:
    """API base URL — overridable through ``ASTROLINKERS_BASE_URL``."""
    return os.environ.get("ASTROLINKERS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def admin_client(founder_token: str, base_url: str) -> Iterator[Astrolinkers]:
    """Founder-scoped client used only to mint + revoke the test key."""
    client = Astrolinkers(
        api_key=founder_token,
        base_url=base_url,
        max_retries=1,
        user_agent_suffix="e2e-smoke",
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="session")
def issued_test_key(admin_client: Astrolinkers) -> Iterator[IssuedApiKey]:
    """Mint a 1-hour test key with broad scopes; revoke on teardown."""
    expires_at = datetime.now(tz=UTC) + timedelta(hours=1)
    key = admin_client.api_keys.issue(
        name=f"sdk-e2e-{int(datetime.now(tz=UTC).timestamp())}",
        scopes=list(TEST_KEY_SCOPES),
        expires_at=expires_at,
        metadata={"purpose": "sdk-e2e-smoke"},
    )
    try:
        yield key
    finally:
        # Best-effort revoke — failure here should not poison the run.
        try:
            admin_client.api_keys.revoke(key.id)
        except (RuntimeError, ValueError, OSError) as exc:
            # Log and swallow: the key auto-expires in an hour anyway.
            print(f"warning: failed to revoke test key {key.id}: {exc}")


@pytest.fixture(scope="session")
def sync_client(
    issued_test_key: IssuedApiKey,
    base_url: str,
) -> Iterator[Astrolinkers]:
    """Sync client bound to the throw-away test key."""
    client = Astrolinkers(
        api_key=issued_test_key.plaintext,
        base_url=base_url,
        max_retries=2,
        read_timeout=180.0,
        user_agent_suffix="e2e-smoke-sync",
    )
    try:
        yield client
    finally:
        client.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_client(
    issued_test_key: IssuedApiKey,
    base_url: str,
) -> AsyncIterator[AsyncAstrolinkers]:
    """Async client bound to the throw-away test key."""
    client = AsyncAstrolinkers(
        api_key=issued_test_key.plaintext,
        base_url=base_url,
        max_retries=2,
        read_timeout=180.0,
        user_agent_suffix="e2e-smoke-async",
    )
    try:
        yield client
    finally:
        await client.aclose()


# ----------------------------------------------------------------------------
# Chart fixtures
# ----------------------------------------------------------------------------


@pytest.fixture(scope="session")
def chart_a(sync_client: Astrolinkers) -> Chart:
    """Primary chart used by every per-chart endpoint."""
    return sync_client.charts.create(
        moment=CHART_A_MOMENT,
        latitude=CHART_A_LAT,
        longitude=CHART_A_LON,
        # Pass ``system`` as a raw string deliberately — exercises the
        # recent enum-widening fix where ``charts.create`` accepts
        # ``AstrologySystem | str``.
        system="vedic",
        house_system=HouseSystem.PLACIDUS,
        ayanamsha=AyanamshaType.LAHIRI,
    )


@pytest.fixture(scope="session")
def chart_b(sync_client: Astrolinkers) -> Chart:
    """Secondary chart, used for compatibility tests."""
    return sync_client.charts.create(
        moment=CHART_B_MOMENT,
        latitude=CHART_B_LAT,
        longitude=CHART_B_LON,
        system=AstrologySystem.VEDIC,
        house_system=HouseSystem.WHOLE_SIGN,
        ayanamsha=AyanamshaType.LAHIRI,
    )
