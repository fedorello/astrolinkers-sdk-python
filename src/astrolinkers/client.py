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

from types import TracebackType
from typing import Self

import httpx

from astrolinkers._settings import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_READ_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    ClientSettings,
)
from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.resources.charts import AsyncCharts, SyncCharts
from astrolinkers.resources.interpretations import (
    AsyncInterpretations,
    SyncInterpretations,
)
from astrolinkers.resources.llm import AsyncLLM, SyncLLM


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
        self.charts = AsyncCharts(self._transport)
        self.llm = AsyncLLM(self._transport)
        self.interpretations = AsyncInterpretations(self._transport)

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
        self.charts = SyncCharts(self._transport)
        self.llm = SyncLLM(self._transport)
        self.interpretations = SyncInterpretations(self._transport)

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
