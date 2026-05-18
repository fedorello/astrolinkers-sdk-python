"""Pydantic models for the feedback + template accuracy loop."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FeedbackVerdict = Literal["correct", "doubtful", "wrong"]
FeedbackRole = Literal["subject", "observer", "hr_admin"]


class FeedbackEntry(BaseModel):
    """One feedback record submitted against a statement.

    Submissions feed the rolling accuracy aggregate for the linked
    template; high-volume templates with a stable verdict bias inform
    template deprecation.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    statement_id: str
    chart_id: str
    template_id: str
    skill_id: str
    verdict: FeedbackVerdict
    role: FeedbackRole
    user_id: str | None = None
    organization_id: str | None = None
    comment: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    submitted_at: datetime


class TemplateAccuracy(BaseModel):
    """Rolling accuracy aggregate for one template."""

    model_config = ConfigDict(extra="allow")

    template_id: str
    sample_size: int
    correct_count: int
    doubtful_count: int
    wrong_count: int
    accuracy: float
    deprecated: bool
    updated_at: datetime
