"""Pydantic model for ``DELETE /v1/tenant/data``."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErasureReport(BaseModel):
    """What erasing all of the account's data removed."""

    model_config = ConfigDict(extra="allow")

    tenant_id: str
    charts_deleted: int
    rows_deleted: int
    rows_by_store: dict[str, int]
    report_files_deleted: int
    cache_entries_deleted: int
