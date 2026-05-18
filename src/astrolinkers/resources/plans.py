"""Plans resource — list catalogue, read + switch the tenant plan."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.plans import Plan, TenantPlan


class AsyncPlans:
    """Async plans resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> list[Plan]:
        """Catalogue of all available plan tiers."""
        data = await self._transport.request("GET", "/v1/plans")
        items = data.get("items", data)
        return [Plan.model_validate(item) for item in items]

    async def get_tenant_plan(self) -> TenantPlan:
        """Plan the calling tenant is currently on."""
        data = await self._transport.request("GET", "/v1/tenant/plan")
        return TenantPlan.model_validate(data)

    async def set_tenant_plan(self, *, plan_tier: str) -> TenantPlan:
        """Switch the calling tenant to a different plan tier."""
        data = await self._transport.request(
            "POST",
            "/v1/tenant/plan",
            json={"plan_tier": plan_tier},
        )
        return TenantPlan.model_validate(data)


class SyncPlans:
    """Sync mirror of :class:`AsyncPlans`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> list[Plan]:
        """Catalogue of all available plan tiers."""
        data = self._transport.request("GET", "/v1/plans")
        items = data.get("items", data)
        return [Plan.model_validate(item) for item in items]

    def get_tenant_plan(self) -> TenantPlan:
        """Plan the calling tenant is currently on."""
        data = self._transport.request("GET", "/v1/tenant/plan")
        return TenantPlan.model_validate(data)

    def set_tenant_plan(self, *, plan_tier: str) -> TenantPlan:
        """Switch the calling tenant to a different plan tier."""
        data = self._transport.request(
            "POST",
            "/v1/tenant/plan",
            json={"plan_tier": plan_tier},
        )
        return TenantPlan.model_validate(data)
