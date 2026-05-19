"""Pydantic models for ``/v1/api-keys`` endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKey(BaseModel):
    """Metadata about an issued API key.

    The plaintext token itself is only returned once at issue time
    via :attr:`IssuedApiKey.plaintext` — store it immediately or you
    will have to revoke and re-issue.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    key_prefix: str
    key_last4: str
    display: str
    scopes: list[str]
    owner_tenant_id: str
    created_at: datetime
    created_by: str
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class IssuedApiKey(BaseModel):
    """Server response from ``POST /v1/api-keys``.

    Flat shape matching ``IssuedApiKeyResponse`` on the wire. The
    ``plaintext`` bearer token is returned exactly once on issue —
    capture it immediately; subsequent ``list`` / ``revoke`` calls
    return :class:`ApiKey` metadata only.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    key_prefix: str
    key_last4: str
    display: str
    scopes: list[str]
    owner_tenant_id: str
    created_at: datetime
    created_by: str
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    plaintext: str
