"""Pydantic models for ``/v1/charts/{chart_id}/profile/talent``."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkillProfile(BaseModel):
    """Talent / hiring-oriented profile derived from a chart.

    The deep payload (``skills`` ranking, ``strengths``, ``risks``,
    etc.) is left untyped because shape evolves with the ontology
    and is iterated by score / id on the consumer side anyway.
    """

    model_config = ConfigDict(extra="allow")

    chart_id: str
    locale: str | None = None
    skills: list[dict[str, Any]] = Field(default_factory=list)
    strengths: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
