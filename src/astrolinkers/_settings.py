"""Client configuration container.

Settings are passed positionally / by keyword to the client
constructor. The defaults mirror the production API so a one-line
``Astrolinkers(api_key=...)`` is enough for the common case.

Keeping this as a plain dataclass (not Pydantic) avoids forcing
callers to depend on a specific Pydantic schema for their wiring —
the SDK itself is the consumer of this object.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.astrolinkers.com"
DEFAULT_TIMEOUT_SECONDS = 60.0
# Streaming and premium-tier calls can take 2 minutes; the read
# timeout is set high so the client does not abort a legitimate
# long-running response.
DEFAULT_READ_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_RETRIES = 2


@dataclass(frozen=True, slots=True)
class ClientSettings:
    """Immutable client configuration.

    Args:
        api_key: Bearer token issued by the Astrolinkers control
            plane. Treat as a secret.
        base_url: API root, without a trailing slash. Override only
            when targeting a non-production environment.
        timeout: Per-request connect / write timeout in seconds.
        read_timeout: Read timeout in seconds — applies to long
            streaming responses. Set to ``None`` to disable.
        max_retries: How many times the transport may retry a
            transient failure (connection / 5xx) before giving up.
            ``0`` disables retry. ``429`` always honours
            ``Retry-After`` and does not count against this budget.
        user_agent_suffix: Extra token appended to the SDK's
            ``User-Agent`` header. Useful when embedding the SDK in
            a higher-level product so server-side logs can correlate.
    """

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    read_timeout: float | None = DEFAULT_READ_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    user_agent_suffix: str | None = None

    def __post_init__(self) -> None:
        """Validate cheaply at construction time."""
        if not self.api_key:
            raise ValueError("api_key must be a non-empty string")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.read_timeout is not None and self.read_timeout <= 0:
            raise ValueError("read_timeout must be positive or None")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
