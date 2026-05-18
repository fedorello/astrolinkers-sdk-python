"""LLM streaming endpoints — SSE parsing into typed events."""

from __future__ import annotations

import httpx
import pytest
import respx

from astrolinkers import (
    Astrolinkers,
    AsyncAstrolinkers,
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
)


def _sse_body() -> bytes:
    """Hand-craft a small but complete SSE stream."""
    return (
        b"event: meta\n"
        b'data: {"kind":"meta","interpretation_type":"theme",'
        b'"language":"en","tier":"basic","engine_context":{"theme":"career"}}\n\n'
        b"event: delta\n"
        b'data: {"kind":"delta","content":"Hello "}\n\n'
        b"event: delta\n"
        b'data: {"kind":"delta","content":"world"}\n\n'
        b"event: done\n"
        b'data: {"kind":"done","input_tokens":100,"output_tokens":250,'
        b'"latency_ms":4200,"cost_usd":0.0021,"interpretation_id":"i-1","cached":false}\n\n'
    )


def _error_stream() -> bytes:
    return (
        b"event: meta\n"
        b'data: {"kind":"meta","interpretation_type":"theme",'
        b'"language":"en","tier":"basic","engine_context":{}}\n\n'
        b"event: delta\n"
        b'data: {"kind":"delta","content":"partial"}\n\n'
        b"event: error\n"
        b'data: {"kind":"error","error":"upstream blew up"}\n\n'
    )


def test_sync_stream_parses_meta_delta_done(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/llm/theme/career/stream").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=_sse_body(),
        ),
    )
    events = list(sync_client.llm.theme_stream(chart_id="c1", theme="career"))
    kinds = [type(e).__name__ for e in events]
    assert kinds == ["MetaEvent", "DeltaEvent", "DeltaEvent", "DoneEvent"]
    meta = events[0]
    assert isinstance(meta, MetaEvent)
    assert meta.engine_context["theme"] == "career"
    deltas = [e for e in events if isinstance(e, DeltaEvent)]
    assert "".join(d.content for d in deltas) == "Hello world"
    done = events[-1]
    assert isinstance(done, DoneEvent)
    assert done.interpretation_id == "i-1"
    assert done.input_tokens == 100
    assert done.output_tokens == 250
    assert done.cost_usd == 0.0021


def test_sync_stream_terminates_on_error_event(
    sync_client: Astrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/llm/theme/career/stream").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=_error_stream(),
        ),
    )
    events = list(sync_client.llm.theme_stream(chart_id="c1", theme="career"))
    assert isinstance(events[-1], ErrorEvent)
    assert events[-1].error == "upstream blew up"
    # No DoneEvent after an ErrorEvent — stream is single-terminator.
    assert not any(isinstance(e, DoneEvent) for e in events)


@pytest.mark.asyncio
async def test_async_stream_parses_full_sequence(
    async_client: AsyncAstrolinkers,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("/v1/llm/chart-reading/stream").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=_sse_body(),
        ),
    )
    events = [ev async for ev in async_client.llm.chart_reading_stream(chart_id="c1")]
    assert isinstance(events[0], MetaEvent)
    assert isinstance(events[-1], DoneEvent)
