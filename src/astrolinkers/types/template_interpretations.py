"""Pydantic models for the template-driven interpretation flow."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Statement(BaseModel):
    """One generated statement inside a template interpretation.

    Statements carry the ``template_id`` and ``skill_id`` they came
    from so the caller can submit feedback that flows back into the
    template's rolling accuracy aggregate.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    template_id: str
    skill_id: str
    text: str
    confidence: float | None = None


class TemplateInterpretation(BaseModel):
    """Output of ``POST /v1/interpretations``."""

    model_config = ConfigDict(extra="allow")

    id: str
    chart_id: str
    locale: str
    tone: str
    statements: list[Statement] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
