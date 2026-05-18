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
from astrolinkers.types.api_keys import ApiKey, IssuedApiKey
from astrolinkers.types.compatibility import (
    CompatibilityAxis,
    CompatibilityReport,
)
from astrolinkers.types.feedback import (
    FeedbackEntry,
    FeedbackRole,
    FeedbackVerdict,
    TemplateAccuracy,
)
from astrolinkers.types.plans import Plan, TenantPlan
from astrolinkers.types.profiles import SkillProfile
from astrolinkers.types.reports import (
    Report,
    ReportFormat,
    ReportKind,
    ReportStatus,
)
from astrolinkers.types.template_interpretations import (
    Statement,
    TemplateInterpretation,
)
from astrolinkers.types.usage_buckets import HourlyUsage, HourlyUsageBucket
from astrolinkers.types.vedic_enums import (
    BhavaStyle,
    HouseSignificator,
    TheoArea,
    Varga,
    VimshopakaGroup,
)

__all__ = [
    # Errors
    "APIError",
    "AstrolinkersError",
    "AuthenticationError",
    "BudgetExceededError",
    "ConnectionError",
    "InvalidRequestError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitedError",
    "ServerError",
    "TimeoutError",
    # Client
    "Astrolinkers",
    "AsyncAstrolinkers",
    # Core types — charts / enums
    "AstrologySystem",
    "AyanamshaType",
    "BirthData",
    "Chart",
    "HouseCusp",
    "HouseSystem",
    "PlanetPosition",
    # LLM / interpretation types
    "DeltaEvent",
    "DoneEvent",
    "ErrorEvent",
    "InterpretationListPage",
    "InterpretationStreamEvent",
    "InterpretationTier",
    "InterpretationType",
    "LLMInterpretation",
    "Language",
    "MetaEvent",
    "StoredLLMInterpretation",
    "UsageBucket",
    "UsageGroupBy",
    "UsageSummary",
    # API keys
    "ApiKey",
    "IssuedApiKey",
    # Compatibility
    "CompatibilityAxis",
    "CompatibilityReport",
    # Feedback
    "FeedbackEntry",
    "FeedbackRole",
    "FeedbackVerdict",
    "TemplateAccuracy",
    # Plans
    "Plan",
    "TenantPlan",
    # Profiles
    "SkillProfile",
    # Reports
    "Report",
    "ReportFormat",
    "ReportKind",
    "ReportStatus",
    # Template interpretations
    "Statement",
    "TemplateInterpretation",
    # Usage buckets
    "HourlyUsage",
    "HourlyUsageBucket",
    # Vedic enums
    "BhavaStyle",
    "HouseSignificator",
    "TheoArea",
    "Varga",
    "VimshopakaGroup",
    # Version
    "__version__",
]
