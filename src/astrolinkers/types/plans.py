"""Pydantic models for ``/v1/plans`` + tenant plan endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Plan(BaseModel):
    """Catalogue entry for one plan tier.

    Mirrors ``PlanResponse`` on the wire — flat fields straight from
    ``GET /v1/plans``. ``llm_cost_cap_per_hour_usd`` is the only
    optional field; everything else is required server-side.
    """

    model_config = ConfigDict(extra="allow")

    tier: str
    display_name: str
    monthly_price_usd: float
    rate_limit_capacity: float
    rate_limit_refill_per_second: float
    llm_cost_cap_per_hour_usd: float | None = None
    status: str
    features: list[str]


class TenantPlan(BaseModel):
    """The plan the calling tenant is currently on.

    Mirrors ``TenantPlanResponse`` on the wire. The plan catalogue
    entry lives under the nested ``plan`` field; top-level fields
    identify the tenant and when their assignment last changed.
    """

    model_config = ConfigDict(extra="allow")

    tenant_id: str
    display_name: str
    plan: Plan
    plan_updated_at: datetime
    created_at: datetime
