"""Pydantic models for ``/v1/api-keys`` endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKey(BaseModel):
    """Metadata about an issued API key.

    The plaintext token itself is **never** returned after issue —
    store :attr:`IssuedApiKey.token` immediately or you will have to
    revoke and re-issue.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class IssuedApiKey(BaseModel):
    """Server response from ``POST /v1/api-keys``.

    The only chance to capture the bearer ``token`` — after this call
    only :class:`ApiKey` metadata is returned by ``list``.
    """

    model_config = ConfigDict(extra="allow")

    api_key: ApiKey
    token: str
