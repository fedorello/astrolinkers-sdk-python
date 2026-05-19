"""Pydantic models for the report-generation pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ReportKind = Literal["talent_lens", "personal_reader"]
ReportFormat = Literal["html", "pdf"]
ReportStatus = Literal["pending", "running", "ready", "failed"]


class Report(BaseModel):
    """Status + artifact URL for a report generation job.

    The artifact URL is populated once :attr:`status` is ``ready``.
    Poll ``client.reports.retrieve(report_id)`` until then; the URL
    is typically a pre-signed S3 link valid for a short window.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    chart_id: str
    kind: ReportKind
    format: ReportFormat
    status: ReportStatus
    artifact_url: str | None = None
    artifact_key: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
