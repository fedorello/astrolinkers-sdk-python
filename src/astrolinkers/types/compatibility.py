"""Pydantic models for compatibility reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CompatibilityAxis = Literal["talent", "romantic", "team"]


class CompatibilityReport(BaseModel):
    """One compatibility report between two charts.

    ``ashtakoota`` (8-fold Vedic kuta) and ``synastry`` (aspect-based
    Western synastry) are returned as raw structured dicts because
    their shape is deep and rarely matched against a model directly;
    callers iterate / index them.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    chart_a_id: str
    chart_b_id: str
    axis: CompatibilityAxis
    verdict: str
    overall_score_percent: float
    ashtakoota: dict[str, Any] | None = None
    synastry: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime
