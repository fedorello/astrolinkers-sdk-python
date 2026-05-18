"""Pydantic models for the ``/usage`` family of endpoints.

Renamed from a more obvious ``usage.py`` only to avoid the in-tree
collision with :mod:`astrolinkers.types.usage` which holds the LLM
``UsageSummary``. The two are different concepts: LLM
``UsageSummary`` aggregates LLM cost / tokens; the hourly buckets
here aggregate raw API hits per key or per tenant.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HourlyUsageBucket(BaseModel):
    """API-call counts in one wall-clock hour."""

    model_config = ConfigDict(frozen=True)

    hour: datetime
    request_count: int
    success_count: int = 0
    error_count: int = 0
    last_request_at: datetime | None = None


class HourlyUsage(BaseModel):
    """Series of hourly buckets returned by the usage endpoints."""

    model_config = ConfigDict(extra="allow")

    buckets: list[HourlyUsageBucket] = Field(default_factory=list)
    total_requests: int = 0
