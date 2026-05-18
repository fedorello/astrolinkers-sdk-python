"""LLM interpretations resource.

Covers the four ``POST /v1/llm/...`` sync endpoints and their
``/stream`` siblings. Streaming methods return an async (or sync)
iterator of typed events.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator, Mapping
from datetime import datetime
from typing import Any

import httpx
import httpx_sse

from astrolinkers._errors import APIError, AstrolinkersError
from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.enums import InterpretationTier, Language, UsageGroupBy
from astrolinkers.types.interpretations import (
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    InterpretationListPage,
    InterpretationStreamEvent,
    LLMInterpretation,
    MetaEvent,
    StoredLLMInterpretation,
)
from astrolinkers.types.usage import UsageSummary


def _list_stored_params(
    *,
    chart_id: str | None,
    interpretation_type: str | None,
    language: Language | None,
    tier: InterpretationTier | None,
    limit: int,
    offset: int,
) -> dict[str, object]:
    """Query for ``GET /v1/llm/interpretations``."""
    return {
        "chart_id": chart_id,
        "interpretation_type": interpretation_type,
        "language": language,
        "tier": tier,
        "limit": limit,
        "offset": offset,
    }


def _usage_params(
    *,
    from_: datetime,
    to: datetime,
    chart_id: str | None,
    interpretation_type: str | None,
    language: Language | None,
    tier: InterpretationTier | None,
    group_by: UsageGroupBy,
) -> dict[str, object]:
    """Query for ``GET /v1/llm/usage-summary``."""
    return {
        "from": from_.isoformat(),
        "to": to.isoformat(),
        "chart_id": chart_id,
        "interpretation_type": interpretation_type,
        "language": language,
        "tier": tier,
        "group_by": group_by,
    }


# ──────────────────────────────────────────────────────────────────
# Query helpers
# ──────────────────────────────────────────────────────────────────


def _theme_params(
    *,
    chart_id: str,
    language: Language,
    tier: InterpretationTier,
    at: datetime | None,
    fresh: bool,
) -> dict[str, object]:
    return {
        "chart_id": chart_id,
        "language": language,
        "tier": tier,
        "at": at.isoformat() if at else None,
        "fresh": fresh or None,
    }


def _chart_reading_params(
    *,
    chart_id: str,
    language: Language,
    tier: InterpretationTier,
    fresh: bool,
) -> dict[str, object]:
    return {
        "chart_id": chart_id,
        "language": language,
        "tier": tier,
        "fresh": fresh or None,
    }


def _dasha_params(
    *,
    chart_id: str,
    language: Language,
    tier: InterpretationTier,
    at: datetime,
    fresh: bool,
) -> dict[str, object]:
    return {
        "chart_id": chart_id,
        "language": language,
        "tier": tier,
        "at": at.isoformat(),
        "fresh": fresh or None,
    }


def _muhurta_params(
    *,
    chart_id: str,
    language: Language,
    tier: InterpretationTier,
    window_start: datetime,
    window_end: datetime,
    interval_minutes: int,
    top_n: int,
    fresh: bool,
) -> dict[str, object]:
    return {
        "chart_id": chart_id,
        "language": language,
        "tier": tier,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "interval_minutes": interval_minutes,
        "top_n": top_n,
        "fresh": fresh or None,
    }


# ──────────────────────────────────────────────────────────────────
# Event parsing — used by both async and sync streams
# ──────────────────────────────────────────────────────────────────

# Header sent with every streaming request. Keeps proxies from
# buffering and tells the server to skip its own caching.
_STREAM_HEADERS: Mapping[str, str] = {"Accept": "text/event-stream"}


def _parse_event(event: httpx_sse.ServerSentEvent) -> InterpretationStreamEvent:
    """Translate a raw SSE event into a typed model.

    The server uses the event name as the discriminator (``meta`` /
    ``delta`` / ``done`` / ``error``) and the JSON payload carries the
    fields. Unknown event names are mapped to :class:`ErrorEvent` with
    a descriptive message so callers always get a terminal-able shape.
    """
    name = event.event or "delta"
    try:
        payload: dict[str, Any] = json.loads(event.data) if event.data else {}
    except json.JSONDecodeError as exc:
        return ErrorEvent(error=f"Malformed event payload: {exc}")
    payload.pop("kind", None)  # Re-derived from the literal in each model.
    if name == "meta":
        return MetaEvent.model_validate(payload)
    if name == "delta":
        return DeltaEvent.model_validate(payload)
    if name == "done":
        return DoneEvent.model_validate(payload)
    if name == "error":
        return ErrorEvent.model_validate(payload)
    return ErrorEvent(error=f"Unknown SSE event: {name!r}")


async def _aiter_events(
    response: httpx.Response,
) -> AsyncIterator[InterpretationStreamEvent]:
    """Async-iterate ``httpx_sse`` events from ``response``.

    Stops as soon as a terminal event (``done`` or ``error``) is
    yielded so the underlying connection is released promptly.
    """
    async for event in httpx_sse.EventSource(response).aiter_sse():
        parsed = _parse_event(event)
        yield parsed
        if isinstance(parsed, (DoneEvent, ErrorEvent)):
            return


def _iter_events(
    response: httpx.Response,
) -> Iterator[InterpretationStreamEvent]:
    """Sync-iterate ``httpx_sse`` events from ``response``."""
    for event in httpx_sse.EventSource(response).iter_sse():
        parsed = _parse_event(event)
        yield parsed
        if isinstance(parsed, (DoneEvent, ErrorEvent)):
            return


# ──────────────────────────────────────────────────────────────────
# Async LLM resource
# ──────────────────────────────────────────────────────────────────


class AsyncLLM:
    """Async access to the LLM endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    # ── Sync (i.e. non-streaming) endpoints ────────────────────────

    async def theme(
        self,
        *,
        chart_id: str,
        theme: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        at: datetime | None = None,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Per-life-area interpretation (career, marriage, wealth, ...)."""
        data = await self._transport.request(
            "POST",
            f"/v1/llm/theme/{theme}",
            params=_theme_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    async def chart_reading(
        self,
        *,
        chart_id: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Full-chart synthesis (meta-factors + yogas + headline themes)."""
        data = await self._transport.request(
            "POST",
            "/v1/llm/chart-reading",
            params=_chart_reading_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    async def dasha_forecast(
        self,
        *,
        chart_id: str,
        at: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Period-aware forecast for a specific moment."""
        data = await self._transport.request(
            "POST",
            "/v1/llm/dasha-forecast",
            params=_dasha_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    async def muhurta_reasoning(
        self,
        *,
        chart_id: str,
        window_start: datetime,
        window_end: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        interval_minutes: int = 60,
        top_n: int = 5,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Electional reasoning over a window of candidate moments."""
        data = await self._transport.request(
            "POST",
            "/v1/llm/muhurta-reasoning",
            params=_muhurta_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                window_start=window_start,
                window_end=window_end,
                interval_minutes=interval_minutes,
                top_n=top_n,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    # ── Streaming endpoints ────────────────────────────────────────

    def theme_stream(
        self,
        *,
        chart_id: str,
        theme: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        at: datetime | None = None,
        fresh: bool = False,
    ) -> AsyncIterator[InterpretationStreamEvent]:
        """Stream a theme interpretation as typed events."""
        return self._stream(
            f"/v1/llm/theme/{theme}/stream",
            _theme_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )

    def chart_reading_stream(
        self,
        *,
        chart_id: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> AsyncIterator[InterpretationStreamEvent]:
        """Stream the full-chart synthesis."""
        return self._stream(
            "/v1/llm/chart-reading/stream",
            _chart_reading_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                fresh=fresh,
            ),
        )

    def dasha_forecast_stream(
        self,
        *,
        chart_id: str,
        at: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> AsyncIterator[InterpretationStreamEvent]:
        """Stream the dasha forecast."""
        return self._stream(
            "/v1/llm/dasha-forecast/stream",
            _dasha_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )

    def muhurta_reasoning_stream(
        self,
        *,
        chart_id: str,
        window_start: datetime,
        window_end: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        interval_minutes: int = 60,
        top_n: int = 5,
        fresh: bool = False,
    ) -> AsyncIterator[InterpretationStreamEvent]:
        """Stream muhurta reasoning."""
        return self._stream(
            "/v1/llm/muhurta-reasoning/stream",
            _muhurta_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                window_start=window_start,
                window_end=window_end,
                interval_minutes=interval_minutes,
                top_n=top_n,
                fresh=fresh,
            ),
        )

    async def _stream(
        self,
        path: str,
        params: Mapping[str, object],
    ) -> AsyncIterator[InterpretationStreamEvent]:
        """Generic streaming worker — shared by every ``*_stream`` method.

        Yields :class:`ErrorEvent` instead of raising mid-stream so
        callers can drain the iterator deterministically; pre-stream
        failures (auth, validation) still raise from the underlying
        transport.
        """
        try:
            async with self._transport.stream(
                "POST",
                path,
                params=params,
                headers=_STREAM_HEADERS,
            ) as response:
                async for ev in _aiter_events(response):
                    yield ev
        except APIError:
            # Pre-stream API error — let it propagate. The caller wants
            # to see "401 not authorised" raised, not buried in a
            # terminal event.
            raise
        except AstrolinkersError as exc:
            yield ErrorEvent(error=str(exc))

    # ── Persistence: list / read past interpretations + usage ────

    async def list_stored(
        self,
        *,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> InterpretationListPage:
        """List previously generated LLM interpretations, newest first."""
        data = await self._transport.request(
            "GET",
            "/v1/llm/interpretations",
            params=_list_stored_params(
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                limit=limit,
                offset=offset,
            ),
        )
        return InterpretationListPage.model_validate(data)

    async def retrieve_stored(
        self,
        interpretation_id: str,
    ) -> StoredLLMInterpretation:
        """Read one stored LLM interpretation by id."""
        data = await self._transport.request(
            "GET",
            f"/v1/llm/interpretations/{interpretation_id}",
        )
        return StoredLLMInterpretation.model_validate(data)

    async def usage_summary(
        self,
        *,
        from_: datetime,
        to: datetime,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        group_by: UsageGroupBy = UsageGroupBy.NONE,
    ) -> UsageSummary:
        """Aggregated call count / tokens / cost over a window."""
        data = await self._transport.request(
            "GET",
            "/v1/llm/usage-summary",
            params=_usage_params(
                from_=from_,
                to=to,
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                group_by=group_by,
            ),
        )
        return UsageSummary.model_validate(data)


# ──────────────────────────────────────────────────────────────────
# Sync LLM resource
# ──────────────────────────────────────────────────────────────────


class SyncLLM:
    """Sync mirror of :class:`AsyncLLM`.

    The streaming methods return a plain :class:`Iterator` so callers
    can simply ``for event in client.llm.theme_stream(...): ...``.
    """

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def theme(
        self,
        *,
        chart_id: str,
        theme: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        at: datetime | None = None,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Per-life-area interpretation."""
        data = self._transport.request(
            "POST",
            f"/v1/llm/theme/{theme}",
            params=_theme_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    def chart_reading(
        self,
        *,
        chart_id: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Full-chart synthesis."""
        data = self._transport.request(
            "POST",
            "/v1/llm/chart-reading",
            params=_chart_reading_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    def dasha_forecast(
        self,
        *,
        chart_id: str,
        at: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Period-aware forecast."""
        data = self._transport.request(
            "POST",
            "/v1/llm/dasha-forecast",
            params=_dasha_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    def muhurta_reasoning(
        self,
        *,
        chart_id: str,
        window_start: datetime,
        window_end: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        interval_minutes: int = 60,
        top_n: int = 5,
        fresh: bool = False,
    ) -> LLMInterpretation:
        """Electional reasoning."""
        data = self._transport.request(
            "POST",
            "/v1/llm/muhurta-reasoning",
            params=_muhurta_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                window_start=window_start,
                window_end=window_end,
                interval_minutes=interval_minutes,
                top_n=top_n,
                fresh=fresh,
            ),
        )
        return LLMInterpretation.model_validate(data)

    def theme_stream(
        self,
        *,
        chart_id: str,
        theme: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        at: datetime | None = None,
        fresh: bool = False,
    ) -> Iterator[InterpretationStreamEvent]:
        """Stream a theme interpretation."""
        return self._stream(
            f"/v1/llm/theme/{theme}/stream",
            _theme_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )

    def chart_reading_stream(
        self,
        *,
        chart_id: str,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> Iterator[InterpretationStreamEvent]:
        """Stream the full-chart synthesis."""
        return self._stream(
            "/v1/llm/chart-reading/stream",
            _chart_reading_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                fresh=fresh,
            ),
        )

    def dasha_forecast_stream(
        self,
        *,
        chart_id: str,
        at: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        fresh: bool = False,
    ) -> Iterator[InterpretationStreamEvent]:
        """Stream the dasha forecast."""
        return self._stream(
            "/v1/llm/dasha-forecast/stream",
            _dasha_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                at=at,
                fresh=fresh,
            ),
        )

    def muhurta_reasoning_stream(
        self,
        *,
        chart_id: str,
        window_start: datetime,
        window_end: datetime,
        language: Language = Language.EN,
        tier: InterpretationTier = InterpretationTier.STANDARD,
        interval_minutes: int = 60,
        top_n: int = 5,
        fresh: bool = False,
    ) -> Iterator[InterpretationStreamEvent]:
        """Stream muhurta reasoning."""
        return self._stream(
            "/v1/llm/muhurta-reasoning/stream",
            _muhurta_params(
                chart_id=chart_id,
                language=language,
                tier=tier,
                window_start=window_start,
                window_end=window_end,
                interval_minutes=interval_minutes,
                top_n=top_n,
                fresh=fresh,
            ),
        )

    def _stream(
        self,
        path: str,
        params: Mapping[str, object],
    ) -> Iterator[InterpretationStreamEvent]:
        try:
            with self._transport.stream(
                "POST",
                path,
                params=params,
                headers=_STREAM_HEADERS,
            ) as response:
                yield from _iter_events(response)
        except APIError:
            raise
        except AstrolinkersError as exc:
            yield ErrorEvent(error=str(exc))

    # ── Persistence: list / read past interpretations + usage ────

    def list_stored(
        self,
        *,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> InterpretationListPage:
        """List previously generated LLM interpretations, newest first."""
        data = self._transport.request(
            "GET",
            "/v1/llm/interpretations",
            params=_list_stored_params(
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                limit=limit,
                offset=offset,
            ),
        )
        return InterpretationListPage.model_validate(data)

    def retrieve_stored(
        self,
        interpretation_id: str,
    ) -> StoredLLMInterpretation:
        """Read one stored LLM interpretation by id."""
        data = self._transport.request(
            "GET",
            f"/v1/llm/interpretations/{interpretation_id}",
        )
        return StoredLLMInterpretation.model_validate(data)

    def usage_summary(
        self,
        *,
        from_: datetime,
        to: datetime,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        group_by: UsageGroupBy = UsageGroupBy.NONE,
    ) -> UsageSummary:
        """Aggregated call count / tokens / cost over a window."""
        data = self._transport.request(
            "GET",
            "/v1/llm/usage-summary",
            params=_usage_params(
                from_=from_,
                to=to,
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                group_by=group_by,
            ),
        )
        return UsageSummary.model_validate(data)
