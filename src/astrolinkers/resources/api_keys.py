"""API keys resource — issue / list / revoke the caller's own keys.

Lets a tenant rotate or scope their own keys without going through
the dashboard. The plaintext bearer token is returned exactly once
on issue (``IssuedApiKey.token``); store it immediately.
"""

from __future__ import annotations

from datetime import datetime

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.api_keys import ApiKey, IssuedApiKey


def _issue_body(
    *,
    name: str,
    scopes: list[str],
    expires_at: datetime | None,
    metadata: dict[str, str] | None,
) -> dict[str, object]:
    body: dict[str, object] = {"name": name, "scopes": scopes}
    if expires_at is not None:
        body["expires_at"] = expires_at.isoformat()
    if metadata is not None:
        body["metadata"] = metadata
    return body


class AsyncApiKeys:
    """Async API-key management."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def issue(
        self,
        *,
        name: str,
        scopes: list[str],
        expires_at: datetime | None = None,
        metadata: dict[str, str] | None = None,
    ) -> IssuedApiKey:
        """Issue a new key. The plaintext ``token`` is in the response."""
        data = await self._transport.request(
            "POST",
            "/v1/api-keys",
            json=_issue_body(
                name=name,
                scopes=scopes,
                expires_at=expires_at,
                metadata=metadata,
            ),
        )
        return IssuedApiKey.model_validate(data)

    async def list(
        self,
        *,
        include_revoked: bool = False,
    ) -> list[ApiKey]:
        """List the caller's keys (active by default)."""
        data = await self._transport.request(
            "GET",
            "/v1/api-keys",
            params={"include_revoked": include_revoked},
        )
        return [ApiKey.model_validate(item) for item in data.get("items", data)]

    async def revoke(self, key_id: str) -> ApiKey:
        """Revoke a key by id. Returns the post-revocation metadata."""
        data = await self._transport.request(
            "POST",
            f"/v1/api-keys/{key_id}/revoke",
        )
        return ApiKey.model_validate(data)


class SyncApiKeys:
    """Sync mirror of :class:`AsyncApiKeys`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def issue(
        self,
        *,
        name: str,
        scopes: list[str],
        expires_at: datetime | None = None,
        metadata: dict[str, str] | None = None,
    ) -> IssuedApiKey:
        """Issue a new key. The plaintext ``token`` is in the response."""
        data = self._transport.request(
            "POST",
            "/v1/api-keys",
            json=_issue_body(
                name=name,
                scopes=scopes,
                expires_at=expires_at,
                metadata=metadata,
            ),
        )
        return IssuedApiKey.model_validate(data)

    def list(
        self,
        *,
        include_revoked: bool = False,
    ) -> list[ApiKey]:
        """List the caller's keys (active by default)."""
        data = self._transport.request(
            "GET",
            "/v1/api-keys",
            params={"include_revoked": include_revoked},
        )
        return [ApiKey.model_validate(item) for item in data.get("items", data)]

    def revoke(self, key_id: str) -> ApiKey:
        """Revoke a key by id. Returns the post-revocation metadata."""
        data = self._transport.request(
            "POST",
            f"/v1/api-keys/{key_id}/revoke",
        )
        return ApiKey.model_validate(data)
