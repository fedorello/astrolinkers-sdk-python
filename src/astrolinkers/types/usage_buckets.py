"""Pydantic models for the ``/usage`` family of endpoints.

Renamed from a more obvious ``usage.py`` only to avoid the in-tree
collision with :mod:`astrolinkers.types.usage` which holds the LLM
``UsageSummary``. The two are different concepts: LLM
``UsageSummary`` aggregates LLM cost / tokens; the hourly buckets
here aggregate raw API hits per key or per tenant.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HourlyUsageBucket(BaseModel):
    """API-call counts in one wall-clock hour.

    Mirrors ``UsageBucketResponse`` on the wire.
    """

    model_config = ConfigDict(frozen=True)

    bucket_hour: datetime
    requests: int
    errors_4xx: int
    errors_5xx: int
    latency_p95_ms: float | None = None


class HourlyUsage(BaseModel):
    """Series of hourly buckets returned by the usage endpoints.

    Mirrors ``UsageRangeResponse`` on the wire.
    """

    model_config = ConfigDict(extra="allow")

    since: datetime
    until: datetime
    total_requests: int
    total_errors: int
    buckets: list[HourlyUsageBucket]
