"""HTTP transport layer.

Encapsulates the ``httpx`` clients (one async, one sync), retry with
exponential backoff, request-id propagation, and the translation of
HTTP errors into the typed :mod:`astrolinkers._errors` hierarchy.

Resources never call ``httpx`` directly — they go through
:class:`AsyncTransport` / :class:`SyncTransport`. This keeps vendor
types confined to one module and lets us swap the HTTP backend
without touching the public API.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from http import HTTPStatus
from typing import Any

import httpx

from astrolinkers._errors import (
    APIError,
    AstrolinkersError,
    AuthenticationError,
    BudgetExceededError,
    ConnectionError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ServerError,
    TimeoutError,
)
from astrolinkers._settings import ClientSettings
from astrolinkers._version import __version__

# HTTP statuses the transport may retry. 429 has its own path that
# honours ``Retry-After`` and does not count against the budget.
_RETRYABLE_STATUSES: frozenset[int] = frozenset({500, 502, 503, 504})

# Backoff schedule: 0.5s -> 1s -> 2s -> 4s with full jitter.
_BACKOFF_BASE_SECONDS = 0.5
_BACKOFF_MAX_SECONDS = 4.0

# Codes the API uses to signal a budget breach (kept in sync with the
# server-side ``LLMBudgetExceeded`` envelope).
_BUDGET_ERROR_CODES: frozenset[str] = frozenset(
    {"llm_budget_exceeded", "budget_exceeded"},
)


def _backoff_seconds(attempt: int) -> float:
    """Compute the delay before the next retry attempt.

    Uses exponential backoff with **full jitter** so concurrent
    clients spread their retries out evenly. ``attempt`` is 1-indexed
    (the first retry passes 1).
    """
    cap = min(_BACKOFF_MAX_SECONDS, _BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
    return random.uniform(0.0, cap)  # noqa: S311 — jitter, not crypto


def _build_user_agent(suffix: str | None) -> str:
    base = f"astrolinkers-python/{__version__}"
    return f"{base} {suffix}" if suffix else base


def _default_headers(settings: ClientSettings) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.api_key}",
        "User-Agent": _build_user_agent(settings.user_agent_suffix),
        "Accept": "application/json",
    }


def _build_timeout(settings: ClientSettings) -> httpx.Timeout:
    """Map :class:`ClientSettings` onto an httpx :class:`Timeout`.

    Connect / write share ``timeout``; read uses the larger
    ``read_timeout`` so streaming responses (>60s for premium-tier
    LLM calls) are not aborted.
    """
    return httpx.Timeout(
        connect=settings.timeout,
        write=settings.timeout,
        read=settings.read_timeout,
        pool=settings.timeout,
    )


def _parse_error_envelope(response: httpx.Response) -> APIError:
    """Translate a non-2xx response into the right ``APIError`` subclass.

    The API always returns the envelope ``{"error": {...}}`` for
    business errors; transports that pre-empt the body (Cloudflare
    error pages, etc.) fall back to a generic message.
    """
    status = response.status_code
    code = "http_error"
    message = response.reason_phrase or "Request failed"
    message_key: str | None = None
    details: dict[str, Any] | None = None
    request_id: str | None = response.headers.get("X-Request-Id")
    try:
        body: Any = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        env = body.get("error")
        if isinstance(env, dict):
            code = str(env.get("code") or code)
            message = str(env.get("message") or message)
            mk = env.get("message_key")
            message_key = str(mk) if isinstance(mk, str) else None
            raw_details = env.get("details")
            if isinstance(raw_details, dict):
                details = dict(raw_details)
            rid = env.get("request_id")
            if isinstance(rid, str):
                request_id = rid

    common: dict[str, Any] = {
        "status_code": status,
        "code": code,
        "message": message,
        "message_key": message_key,
        "details": details,
        "request_id": request_id,
    }

    if code in _BUDGET_ERROR_CODES:
        return BudgetExceededError(**common)
    cls = _STATUS_TO_EXCEPTION.get(status)
    if cls is RateLimitedError:
        retry_after = _extract_retry_after(response, details)
        return RateLimitedError(retry_after_seconds=retry_after, **common)
    if cls is not None:
        return cls(**common)
    if HTTPStatus.BAD_REQUEST <= status < HTTPStatus.INTERNAL_SERVER_ERROR:
        return InvalidRequestError(**common)
    if HTTPStatus.INTERNAL_SERVER_ERROR <= status < 600:  # noqa: PLR2004
        return ServerError(**common)
    return APIError(**common)


# Direct HTTP-status → exception mapping. Keep the table at module
# scope so it's built once.
_STATUS_TO_EXCEPTION: dict[int, type[APIError]] = {
    HTTPStatus.UNAUTHORIZED: AuthenticationError,
    HTTPStatus.FORBIDDEN: PermissionDeniedError,
    HTTPStatus.NOT_FOUND: NotFoundError,
    HTTPStatus.TOO_MANY_REQUESTS: RateLimitedError,
}


def _extract_retry_after(
    response: httpx.Response,
    details: dict[str, Any] | None,
) -> float | None:
    """Read ``Retry-After`` from the response.

    Tries the standard header first (RFC 7231) — value is in seconds,
    integer. Falls back to ``details.retry_after_seconds`` from the
    body so older error envelopes still work.
    """
    header = response.headers.get("Retry-After")
    if header is not None:
        try:
            return float(header)
        except ValueError:
            pass  # Not a delta-seconds value; ignore and try the body.
    if details is not None:
        body_value = details.get("retry_after_seconds")
        if isinstance(body_value, (int, float)):
            return float(body_value)
    return None


def _wrap_network_error(exc: httpx.RequestError) -> AstrolinkersError:
    """Translate transport-level failures into typed exceptions."""
    if isinstance(exc, httpx.TimeoutException):
        return TimeoutError(str(exc))
    return ConnectionError(str(exc))


# ────────────────────────────────────────────────────────────────────
# Async transport
# ────────────────────────────────────────────────────────────────────


class AsyncTransport:
    """Async HTTP layer used by every resource on :class:`AsyncAstrolinkers`."""

    def __init__(
        self,
        settings: ClientSettings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialise the transport.

        Args:
            settings: Frozen :class:`ClientSettings` for this client.
            http_client: Optional pre-built ``httpx.AsyncClient`` used
                during testing (e.g. with ``respx.MockRouter``). When
                ``None`` the transport owns and closes its own client.
        """
        self._settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.base_url,
            headers=_default_headers(settings),
            timeout=_build_timeout(settings),
        )

    @property
    def settings(self) -> ClientSettings:
        return self._settings

    async def aclose(self) -> None:
        """Close the underlying HTTP client if we own it."""
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a JSON request and return the parsed JSON body.

        ``params`` values that are ``None`` are dropped so callers can
        forward optional query parameters uniformly. Returns ``None``
        for 204 responses.
        """
        response = await self._send(method, path, params, json, headers)
        if response.status_code == HTTPStatus.NO_CONTENT:
            return None
        # Empty body on a 2xx is rare but possible; treat as ``None``.
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise AstrolinkersError(
                f"Server returned non-JSON body ({len(response.content)} bytes).",
            ) from exc

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncIterator[httpx.Response]:
        """Open a streaming response. Yields an ``httpx.Response``.

        The caller is expected to iterate the response body (e.g.
        through ``httpx_sse``) inside the context manager. Errors
        before the response opens are mapped to the typed hierarchy;
        errors *during* streaming are raised back to the iterator and
        the SDK's stream consumer translates them into ``ErrorEvent``.
        """
        cleaned_params = _clean_params(params)
        merged_headers = self._merged_headers(headers)
        attempt = 0
        while True:
            attempt += 1
            try:
                async with self._client.stream(
                    method,
                    path,
                    params=cleaned_params,
                    json=json,
                    headers=merged_headers,
                ) as response:
                    if response.status_code >= HTTPStatus.BAD_REQUEST:
                        # Read body so error parsing has access to it.
                        await response.aread()
                        if self._should_retry(response.status_code, attempt):
                            await asyncio.sleep(_backoff_seconds(attempt))
                            continue
                        raise _parse_error_envelope(response)
                    yield response
                    return
            except httpx.RequestError as exc:
                if attempt > self._settings.max_retries:
                    raise _wrap_network_error(exc) from exc
                await asyncio.sleep(_backoff_seconds(attempt))

    async def _send(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None,
        json: Any | None,
        extra_headers: Mapping[str, str] | None,
    ) -> httpx.Response:
        cleaned_params = _clean_params(params)
        merged_headers = self._merged_headers(extra_headers)
        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=cleaned_params,
                    json=json,
                    headers=merged_headers,
                )
            except httpx.RequestError as exc:
                if attempt > self._settings.max_retries:
                    raise _wrap_network_error(exc) from exc
                await asyncio.sleep(_backoff_seconds(attempt))
                continue
            if response.status_code >= HTTPStatus.BAD_REQUEST:
                if self._should_retry(response.status_code, attempt):
                    await asyncio.sleep(_backoff_seconds(attempt))
                    continue
                raise _parse_error_envelope(response)
            return response

    def _should_retry(self, status: int, attempt: int) -> bool:
        if attempt > self._settings.max_retries:
            return False
        return status in _RETRYABLE_STATUSES

    def _merged_headers(
        self,
        extra: Mapping[str, str] | None,
    ) -> dict[str, str] | None:
        if not extra:
            return None
        # httpx merges defaults from the client; we only pass per-call
        # overrides so user-supplied headers can extend the defaults
        # without rebuilding them.
        return dict(extra)


# ────────────────────────────────────────────────────────────────────
# Sync transport
# ────────────────────────────────────────────────────────────────────


class SyncTransport:
    """Sync HTTP layer used by every resource on :class:`Astrolinkers`.

    Behaviour mirrors :class:`AsyncTransport` line-for-line; the only
    difference is the surrounding event-loop. Two implementations
    instead of one ``asyncio.run`` wrapper keeps stacks readable and
    avoids the well-known nested-loop pitfalls in notebooks.
    """

    def __init__(
        self,
        settings: ClientSettings,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=settings.base_url,
            headers=_default_headers(settings),
            timeout=_build_timeout(settings),
        )

    @property
    def settings(self) -> ClientSettings:
        return self._settings

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        response = self._send(method, path, params, json, headers)
        if response.status_code == HTTPStatus.NO_CONTENT:
            return None
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise AstrolinkersError(
                f"Server returned non-JSON body ({len(response.content)} bytes).",
            ) from exc

    @contextmanager
    def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[httpx.Response]:
        cleaned_params = _clean_params(params)
        merged_headers = headers
        attempt = 0
        while True:
            attempt += 1
            try:
                with self._client.stream(
                    method,
                    path,
                    params=cleaned_params,
                    json=json,
                    headers=merged_headers,
                ) as response:
                    if response.status_code >= HTTPStatus.BAD_REQUEST:
                        response.read()
                        if self._should_retry(response.status_code, attempt):
                            time.sleep(_backoff_seconds(attempt))
                            continue
                        raise _parse_error_envelope(response)
                    yield response
                    return
            except httpx.RequestError as exc:
                if attempt > self._settings.max_retries:
                    raise _wrap_network_error(exc) from exc
                time.sleep(_backoff_seconds(attempt))

    def _send(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None,
        json: Any | None,
        extra_headers: Mapping[str, str] | None,
    ) -> httpx.Response:
        cleaned_params = _clean_params(params)
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._client.request(
                    method,
                    path,
                    params=cleaned_params,
                    json=json,
                    headers=extra_headers,
                )
            except httpx.RequestError as exc:
                if attempt > self._settings.max_retries:
                    raise _wrap_network_error(exc) from exc
                time.sleep(_backoff_seconds(attempt))
                continue
            if response.status_code >= HTTPStatus.BAD_REQUEST:
                if self._should_retry(response.status_code, attempt):
                    time.sleep(_backoff_seconds(attempt))
                    continue
                raise _parse_error_envelope(response)
            return response

    def _should_retry(self, status: int, attempt: int) -> bool:
        if attempt > self._settings.max_retries:
            return False
        return status in _RETRYABLE_STATUSES


def _clean_params(
    params: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Drop ``None`` values so optional query params are simply absent.

    Also unwraps ``Enum`` values to their string form, which keeps
    callers from having to write ``language.value`` everywhere.
    """
    if params is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if hasattr(value, "value"):
            cleaned[key] = value.value
        else:
            cleaned[key] = value
    return cleaned or None
