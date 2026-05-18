"""Public client facades.

Two near-identical surfaces exposed for both worlds:

* :class:`AsyncAstrolinkers` — async first; preferred for FastAPI,
  ASGI apps, agent runtimes.
* :class:`Astrolinkers` — sync; ideal for scripts, notebooks,
  Django-style request handlers, AWS Lambda Python runtimes.

Both share the same resource methods so code can be ported between
them with no signature changes.

Usage::

    from astrolinkers import Astrolinkers

    client = Astrolinkers(api_key="alk_live_...")
    reading = client.llm.chart_reading(chart_id=chart.id, tier="premium")
    print(reading.content)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from types import TracebackType
from typing import Any, Self

import httpx

from astrolinkers._settings import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_READ_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    ClientSettings,
)
from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.resources.api_keys import AsyncApiKeys, SyncApiKeys
from astrolinkers.resources.charts import AsyncCharts, SyncCharts
from astrolinkers.resources.compatibility import (
    AsyncCompatibility,
    SyncCompatibility,
)
from astrolinkers.resources.feedback import AsyncFeedback, SyncFeedback
from astrolinkers.resources.health import AsyncHealth, SyncHealth
from astrolinkers.resources.interpretations import (
    AsyncInterpretations,
    SyncInterpretations,
)
from astrolinkers.resources.llm import AsyncLLM, SyncLLM
from astrolinkers.resources.plans import AsyncPlans, SyncPlans
from astrolinkers.resources.profiles import AsyncProfiles, SyncProfiles
from astrolinkers.resources.reports import AsyncReports, SyncReports
from astrolinkers.resources.usage import AsyncUsage, SyncUsage
from astrolinkers.resources.vedic import AsyncVedic, SyncVedic


class AsyncAstrolinkers:
    """Async API client.

    Construct once per process / async context. The client manages
    an underlying ``httpx.AsyncClient`` with a connection pool — long-
    lived reuse is intentional, repeated construction defeats the
    pool and costs latency.

    Args:
        api_key: Bearer token issued by Astrolinkers.
        base_url: Override the API endpoint (rarely needed).
        timeout: Connect / write timeout in seconds.
        read_timeout: Read timeout (long for premium-tier streams).
        max_retries: How many times to retry transient failures.
        user_agent_suffix: Optional product token appended to
            ``User-Agent`` for server-side correlation.
        http_client: Inject a pre-built ``httpx.AsyncClient``. Used
            mainly by tests so ``respx`` can mount.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        read_timeout: float | None = DEFAULT_READ_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent_suffix: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = ClientSettings(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            read_timeout=read_timeout,
            max_retries=max_retries,
            user_agent_suffix=user_agent_suffix,
        )
        self._transport = AsyncTransport(settings, http_client=http_client)
        self.api_keys = AsyncApiKeys(self._transport)
        self.charts = AsyncCharts(self._transport)
        self.compatibility = AsyncCompatibility(self._transport)
        self.feedback = AsyncFeedback(self._transport)
        self.health = AsyncHealth(self._transport)
        self.interpretations = AsyncInterpretations(self._transport)
        self.llm = AsyncLLM(self._transport)
        self.plans = AsyncPlans(self._transport)
        self.profiles = AsyncProfiles(self._transport)
        self.reports = AsyncReports(self._transport)
        self.usage = AsyncUsage(self._transport)
        self.vedic = AsyncVedic(self._transport)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Escape hatch — make an arbitrary authenticated API call.

        Use this when a server endpoint exists that the SDK does not
        wrap yet. Errors map into the same typed hierarchy as the
        resource methods (``AuthenticationError`` / ``RateLimitedError``
        / etc.) and the JSON body is parsed and returned as-is.

        Returns ``None`` for 204 / empty responses.
        """
        return await self._transport.request(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        )

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncIterator[httpx.Response]:
        """Escape hatch for streaming responses.

        Yields the raw ``httpx.Response``; the caller drains the body
        (e.g. ``async for chunk in resp.aiter_bytes()``). The retry +
        error-mapping behaviour matches :meth:`request`.
        """
        async with self._transport.stream(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        ) as response:
            yield response

    async def aclose(self) -> None:
        """Release the underlying HTTP connection pool."""
        await self._transport.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()


class Astrolinkers:
    """Sync API client. See :class:`AsyncAstrolinkers` for argument docs."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        read_timeout: float | None = DEFAULT_READ_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent_suffix: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = ClientSettings(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            read_timeout=read_timeout,
            max_retries=max_retries,
            user_agent_suffix=user_agent_suffix,
        )
        self._transport = SyncTransport(settings, http_client=http_client)
        self.api_keys = SyncApiKeys(self._transport)
        self.charts = SyncCharts(self._transport)
        self.compatibility = SyncCompatibility(self._transport)
        self.feedback = SyncFeedback(self._transport)
        self.health = SyncHealth(self._transport)
        self.interpretations = SyncInterpretations(self._transport)
        self.llm = SyncLLM(self._transport)
        self.plans = SyncPlans(self._transport)
        self.profiles = SyncProfiles(self._transport)
        self.reports = SyncReports(self._transport)
        self.usage = SyncUsage(self._transport)
        self.vedic = SyncVedic(self._transport)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Escape hatch — make an arbitrary authenticated API call.

        Use this when a server endpoint exists that the SDK does not
        wrap yet. Errors map into the same typed hierarchy as the
        resource methods.
        """
        return self._transport.request(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        )

    @contextmanager
    def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[httpx.Response]:
        """Escape hatch for streaming responses."""
        with self._transport.stream(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        ) as response:
            yield response

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._transport.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
