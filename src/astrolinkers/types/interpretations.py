"""Pydantic models for LLM interpretations and the streaming protocol.

Two flavours of model are exported:

* :class:`LLMInterpretation` — the immediate response from a sync
  ``/v1/llm/...`` POST call.
* :class:`StoredLLMInterpretation` — a record fetched from
  ``GET /v1/llm/interpretations/{id}`` (carries ``created_at`` and
  ``request_params``; immutable).
* :class:`InterpretationStreamEvent` and its discriminated subtypes
  (:class:`MetaEvent`, :class:`DeltaEvent`, :class:`DoneEvent`,
  :class:`ErrorEvent`) — yielded by the streaming methods.

The streaming events are typed with a discriminated union so callers
can do ``match event: case MetaEvent(): ...`` exhaustively.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from astrolinkers.types.enums import InterpretationTier, InterpretationType, Language


class LLMInterpretation(BaseModel):
    """In-flight response from a sync ``/v1/llm/...`` POST."""

    model_config = ConfigDict(extra="allow")

    # Widened to ``InterpretationType | str`` so future server-side
    # variants do not raise ``ValidationError`` on parse — callers
    # can still narrow against the enum's known values.
    interpretation_type: InterpretationType | str
    language: Language
    tier: InterpretationTier
    content: str
    engine_context: dict[str, Any] = Field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    # Identifier of the persisted record; empty when persistence is
    # disabled server-side (only relevant in dev / test envs).
    interpretation_id: str = ""
    # Whether the response was replayed from the cache instead of a
    # fresh LLM call.
    cached: bool = False


class StoredLLMInterpretation(BaseModel):
    """A persisted interpretation, fetched after the fact."""

    model_config = ConfigDict(extra="allow")

    id: str
    chart_id: str
    interpretation_type: InterpretationType
    theme: str | None = None  # populated only for ``theme`` interpretations
    language: Language
    tier: InterpretationTier
    content: str
    engine_context: dict[str, Any] = Field(default_factory=dict)
    request_params: dict[str, Any] = Field(default_factory=dict)
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float
    created_at: datetime


class InterpretationListPage(BaseModel):
    """One page of :class:`StoredLLMInterpretation` rows."""

    model_config = ConfigDict(extra="allow")

    items: list[StoredLLMInterpretation]
    total: int
    limit: int
    offset: int


# ──────────────────────────────────────────────────────────────────
# Streaming events
# ──────────────────────────────────────────────────────────────────

# Each event has a ``kind`` literal so the union is discriminated and
# IDE / mypy can narrow inside ``match`` / ``isinstance`` branches.


class MetaEvent(BaseModel):
    """First event of a stream — carries the engine context."""

    model_config = ConfigDict(extra="allow")

    kind: Literal["meta"] = "meta"
    interpretation_type: InterpretationType
    language: Language
    tier: InterpretationTier
    engine_context: dict[str, Any] = Field(default_factory=dict)


class DeltaEvent(BaseModel):
    """Incremental chunk of generated content."""

    model_config = ConfigDict(extra="allow")

    kind: Literal["delta"] = "delta"
    content: str


class DoneEvent(BaseModel):
    """Terminal event with usage accounting + persisted record id."""

    model_config = ConfigDict(extra="allow")

    kind: Literal["done"] = "done"
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    interpretation_id: str = ""
    cached: bool = False


class ErrorEvent(BaseModel):
    """Terminal event indicating a mid-stream failure."""

    model_config = ConfigDict(extra="allow")

    kind: Literal["error"] = "error"
    error: str | None = None


InterpretationStreamEvent = MetaEvent | DeltaEvent | DoneEvent | ErrorEvent
