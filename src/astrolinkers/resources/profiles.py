"""Profiles resource — talent / hiring profile from a chart."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.profiles import SkillProfile


class AsyncProfiles:
    """Async profiles resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def talent(self, chart_id: str) -> SkillProfile:
        """Skill profile for the talent / hiring use-case."""
        data = await self._transport.request(
            "GET",
            f"/v1/charts/{chart_id}/profile/talent",
        )
        return SkillProfile.model_validate(data)


class SyncProfiles:
    """Sync mirror of :class:`AsyncProfiles`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def talent(self, chart_id: str) -> SkillProfile:
        """Skill profile for the talent / hiring use-case."""
        data = self._transport.request(
            "GET",
            f"/v1/charts/{chart_id}/profile/talent",
        )
        return SkillProfile.model_validate(data)
