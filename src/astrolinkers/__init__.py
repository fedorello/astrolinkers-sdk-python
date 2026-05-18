"""Astrolinkers — official Python SDK.

Quick start::

    from astrolinkers import Astrolinkers
    from datetime import datetime, UTC

    client = Astrolinkers(api_key="alk_live_…")
    chart = client.charts.create(
        moment=datetime(1990, 4, 15, 2, 0, tzinfo=UTC),
        latitude=28.6139, longitude=77.2090,
        timezone="Asia/Kolkata",
    )
    reading = client.llm.chart_reading(chart_id=chart.id, tier="premium")
    print(reading.content)

See https://docs.astrolinkers.com for the full reference.
"""

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
from astrolinkers._version import __version__
from astrolinkers.client import Astrolinkers, AsyncAstrolinkers
from astrolinkers.types import (
    AstrologySystem,
    AyanamshaType,
    BirthData,
    Chart,
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    HouseCusp,
    HouseSystem,
    InterpretationListPage,
    InterpretationStreamEvent,
    InterpretationTier,
    InterpretationType,
    Language,
    LLMInterpretation,
    MetaEvent,
    PlanetPosition,
    StoredLLMInterpretation,
    UsageBucket,
    UsageGroupBy,
    UsageSummary,
)

__all__ = [
    "APIError",
    "Astrolinkers",
    "AstrolinkersError",
    "AstrologySystem",
    "AsyncAstrolinkers",
    "AuthenticationError",
    "AyanamshaType",
    "BirthData",
    "BudgetExceededError",
    "Chart",
    "ConnectionError",
    "DeltaEvent",
    "DoneEvent",
    "ErrorEvent",
    "HouseCusp",
    "HouseSystem",
    "InterpretationListPage",
    "InterpretationStreamEvent",
    "InterpretationTier",
    "InterpretationType",
    "InvalidRequestError",
    "LLMInterpretation",
    "Language",
    "MetaEvent",
    "NotFoundError",
    "PermissionDeniedError",
    "PlanetPosition",
    "RateLimitedError",
    "ServerError",
    "StoredLLMInterpretation",
    "TimeoutError",
    "UsageBucket",
    "UsageGroupBy",
    "UsageSummary",
    "__version__",
]

# Marker file (PEP 561) so ``mypy`` / IDEs treat us as fully typed.
# The actual ``py.typed`` file is shipped alongside the package.
