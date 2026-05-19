"""Pydantic models for ``/v1/charts/{chart_id}/profile/talent``."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SkillScore(BaseModel):
    """One scored skill inside a :class:`SkillProfile`.

    Mirrors ``SkillScoreDTO`` on the wire. ``contributing_rules``
    lists the rule ids that fired to produce this score so callers
    can trace the reasoning back to the ontology.
    """

    model_config = ConfigDict(extra="allow")

    skill_id: str
    value: float
    level: str
    contributing_rules: list[str]


class SkillProfile(BaseModel):
    """Talent / hiring-oriented profile derived from a chart.

    Mirrors ``SkillProfileResponse`` on the wire — a list of scored
    skills with ontology trace.
    """

    model_config = ConfigDict(extra="allow")

    chart_id: str
    scores: list[SkillScore]
