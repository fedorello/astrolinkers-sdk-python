"""Pydantic models for ``GET /v1/llm/usage-summary``."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UsageBucket(BaseModel):
    """One row of a usage aggregate — total or break-down bucket."""

    model_config = ConfigDict(frozen=True)

    label: str | None
    call_count: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


class UsageSummary(BaseModel):
    """Aggregated LLM spend over a time window."""

    model_config = ConfigDict(extra="allow")

    # The API serialises the lower bound as ``from`` (a Python keyword),
    # so we alias to ``from_`` for Python-side usage.
    from_: datetime = Field(..., alias="from_")
    to: datetime
    group_by: str
    total: UsageBucket
    breakdown: list[UsageBucket] = Field(default_factory=list)
