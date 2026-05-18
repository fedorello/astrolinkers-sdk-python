"""Reports resource — async report generation pipeline."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.reports import Report, ReportFormat, ReportKind


def _create_body(
    *,
    chart_id: str,
    kind: ReportKind,
    format: ReportFormat,
    locale: str,
    tone: str,
) -> dict[str, object]:
    return {
        "chart_id": chart_id,
        "kind": kind,
        "format": format,
        "locale": locale,
        "tone": tone,
    }


class AsyncReports:
    """Async reports resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        chart_id: str,
        kind: ReportKind = "talent_lens",
        format: ReportFormat = "html",
        locale: str = "en",
        tone: str = "corporate",
    ) -> Report:
        """Enqueue a report generation job; poll ``retrieve`` for completion."""
        data = await self._transport.request(
            "POST",
            "/v1/reports",
            json=_create_body(
                chart_id=chart_id,
                kind=kind,
                format=format,
                locale=locale,
                tone=tone,
            ),
        )
        return Report.model_validate(data)

    async def retrieve(self, report_id: str) -> Report:
        """Read the current status + artifact URL for a report."""
        data = await self._transport.request("GET", f"/v1/reports/{report_id}")
        return Report.model_validate(data)


class SyncReports:
    """Sync mirror of :class:`AsyncReports`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        chart_id: str,
        kind: ReportKind = "talent_lens",
        format: ReportFormat = "html",
        locale: str = "en",
        tone: str = "corporate",
    ) -> Report:
        """Enqueue a report generation job; poll ``retrieve`` for completion."""
        data = self._transport.request(
            "POST",
            "/v1/reports",
            json=_create_body(
                chart_id=chart_id,
                kind=kind,
                format=format,
                locale=locale,
                tone=tone,
            ),
        )
        return Report.model_validate(data)

    def retrieve(self, report_id: str) -> Report:
        """Read the current status + artifact URL for a report."""
        data = self._transport.request("GET", f"/v1/reports/{report_id}")
        return Report.model_validate(data)
