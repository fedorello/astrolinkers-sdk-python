"""Stored interpretations resource and usage summary.

Wraps ``GET /v1/llm/interpretations``, ``GET /v1/llm/interpretations/{id}``
and ``GET /v1/llm/usage-summary``. The LLM-generating endpoints
(``POST /v1/llm/...``) live in :mod:`astrolinkers.resources.llm`.
"""

from __future__ import annotations

from datetime import datetime

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.enums import (
    InterpretationTier,
    Language,
    UsageGroupBy,
)
from astrolinkers.types.interpretations import (
    InterpretationListPage,
    StoredLLMInterpretation,
)
from astrolinkers.types.usage import UsageSummary


def _list_params(
    *,
    chart_id: str | None,
    interpretation_type: str | None,
    language: Language | None,
    tier: InterpretationTier | None,
    limit: int,
    offset: int,
) -> dict[str, object]:
    """Build the query string for the list endpoint."""
    return {
        "chart_id": chart_id,
        "interpretation_type": interpretation_type,
        "language": language,
        "tier": tier,
        "limit": limit,
        "offset": offset,
    }


def _usage_params(
    *,
    from_: datetime,
    to: datetime,
    chart_id: str | None,
    interpretation_type: str | None,
    language: Language | None,
    tier: InterpretationTier | None,
    group_by: UsageGroupBy,
) -> dict[str, object]:
    """Build the query string for the usage-summary endpoint."""
    return {
        "from": from_.isoformat(),
        "to": to.isoformat(),
        "chart_id": chart_id,
        "interpretation_type": interpretation_type,
        "language": language,
        "tier": tier,
        "group_by": group_by,
    }


class AsyncInterpretations:
    """Async stored-interpretations resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(
        self,
        *,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> InterpretationListPage:
        """List the tenant's stored interpretations, newest first."""
        data = await self._transport.request(
            "GET",
            "/v1/llm/interpretations",
            params=_list_params(
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                limit=limit,
                offset=offset,
            ),
        )
        return InterpretationListPage.model_validate(data)

    async def retrieve(self, interpretation_id: str) -> StoredLLMInterpretation:
        """Read one stored interpretation by id."""
        data = await self._transport.request(
            "GET",
            f"/v1/llm/interpretations/{interpretation_id}",
        )
        return StoredLLMInterpretation.model_validate(data)

    async def usage_summary(
        self,
        *,
        from_: datetime,
        to: datetime,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        group_by: UsageGroupBy = UsageGroupBy.NONE,
    ) -> UsageSummary:
        """Aggregate call count / tokens / cost over a window."""
        data = await self._transport.request(
            "GET",
            "/v1/llm/usage-summary",
            params=_usage_params(
                from_=from_,
                to=to,
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                group_by=group_by,
            ),
        )
        return UsageSummary.model_validate(data)


class SyncInterpretations:
    """Sync mirror of :class:`AsyncInterpretations`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> InterpretationListPage:
        """List the tenant's stored interpretations, newest first."""
        data = self._transport.request(
            "GET",
            "/v1/llm/interpretations",
            params=_list_params(
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                limit=limit,
                offset=offset,
            ),
        )
        return InterpretationListPage.model_validate(data)

    def retrieve(self, interpretation_id: str) -> StoredLLMInterpretation:
        """Read one stored interpretation by id."""
        data = self._transport.request(
            "GET",
            f"/v1/llm/interpretations/{interpretation_id}",
        )
        return StoredLLMInterpretation.model_validate(data)

    def usage_summary(
        self,
        *,
        from_: datetime,
        to: datetime,
        chart_id: str | None = None,
        interpretation_type: str | None = None,
        language: Language | None = None,
        tier: InterpretationTier | None = None,
        group_by: UsageGroupBy = UsageGroupBy.NONE,
    ) -> UsageSummary:
        """Aggregate call count / tokens / cost over a window."""
        data = self._transport.request(
            "GET",
            "/v1/llm/usage-summary",
            params=_usage_params(
                from_=from_,
                to=to,
                chart_id=chart_id,
                interpretation_type=interpretation_type,
                language=language,
                tier=tier,
                group_by=group_by,
            ),
        )
        return UsageSummary.model_validate(data)
