"""Typed exception hierarchy raised by the SDK.

The hierarchy mirrors the HTTP semantics so callers can pattern-match
on a specific failure mode without parsing strings:

* :class:`AstrolinkersError`        — base for every SDK exception.
* :class:`APIError`                 — the server replied with an
  error envelope; subclasses below pick the right HTTP status range.
* :class:`AuthenticationError`      — 401.
* :class:`PermissionDeniedError`    — 403.
* :class:`NotFoundError`            — 404.
* :class:`InvalidRequestError`      — 422 / other 4xx without a more
  specific subclass.
* :class:`RateLimitedError`         — 429 with ``Retry-After``.
* :class:`BudgetExceededError`      — 402 / 429 when the cost cap
  triggered (carries ``cap_usd`` / ``spent_usd``).
* :class:`ServerError`              — 5xx.
* :class:`ConnectionError`          — TCP/TLS/DNS or aborted
  connection; the request never reached the server.
* :class:`TimeoutError`             — request or read timed out.

The transport layer maps every failure into one of these so the
public API never leaks ``httpx`` exceptions.
"""

from __future__ import annotations

from typing import Any


class AstrolinkersError(Exception):
    """Base class for every SDK exception."""


class APIError(AstrolinkersError):
    """Server replied with a structured error envelope.

    Attributes:
        status_code: HTTP status of the failed response.
        code: Machine-readable error code from the envelope.
        message: Human-readable message from the envelope.
        message_key: i18n key for client-side translation.
        details: Optional structured detail block.
        request_id: Request id echoed by the server, when available.
    """

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        message_key: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(f"[{status_code} {code}] {message}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.message_key = message_key
        self.details = details or {}
        self.request_id = request_id


class AuthenticationError(APIError):
    """HTTP 401 — missing or invalid bearer token."""


class PermissionDeniedError(APIError):
    """HTTP 403 — token lacks the required scope."""


class NotFoundError(APIError):
    """HTTP 404.

    The requested resource does not exist (or is not visible to the
    calling tenant — the server returns 404 in both cases on purpose).
    """


class InvalidRequestError(APIError):
    """HTTP 4xx other than the above — usually 422 validation errors."""


class RateLimitedError(APIError):
    """HTTP 429 — the per-tenant / per-tier rate limit was hit.

    ``retry_after_seconds`` is sourced from the ``Retry-After`` header
    first and falls back to ``details.retry_after_seconds`` from the
    body — whichever the server populated.
    """

    def __init__(
        self,
        *,
        retry_after_seconds: float | None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.retry_after_seconds = retry_after_seconds


class BudgetExceededError(APIError):
    """The tenant's rolling LLM spend cap was exhausted.

    Carries ``cap_usd`` and ``spent_usd`` when the server provides
    them, so the caller can show the user a top-up prompt with the
    real numbers.
    """

    @property
    def cap_usd(self) -> float | None:
        value = self.details.get("cap_usd")
        return float(value) if value is not None else None

    @property
    def spent_usd(self) -> float | None:
        value = self.details.get("spent_usd")
        return float(value) if value is not None else None


class ServerError(APIError):
    """HTTP 5xx — server-side failure, retryable."""


class ConnectionError(AstrolinkersError):
    """Underlying network failed before the response could be read."""


class TimeoutError(AstrolinkersError):
    """Request, connection, or read deadline elapsed."""
