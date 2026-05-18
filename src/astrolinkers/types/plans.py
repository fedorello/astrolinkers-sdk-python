"""Pydantic models for ``/v1/plans`` + tenant plan endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Plan(BaseModel):
    """Catalogue entry for one plan tier."""

    model_config = ConfigDict(extra="allow")

    tier: str
    name: str
    monthly_price_usd: float | None = None
    monthly_call_cap: int | None = None
    features: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantPlan(BaseModel):
    """The plan the calling tenant is currently on."""

    model_config = ConfigDict(extra="allow")

    tier: str
    activated_at: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
