"""Enumerations used across the API.

All values are kept stable so they are safe to compare against
string literals coming from older code. New variants are added at
the bottom of each enum.
"""

from __future__ import annotations

from enum import StrEnum


class Language(StrEnum):
    """ISO 639-1 code of the language the LLM should answer in."""

    EN = "en"  # English
    HI = "hi"  # Hindi
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    KN = "kn"  # Kannada
    ML = "ml"  # Malayalam
    MR = "mr"  # Marathi
    BN = "bn"  # Bengali
    GU = "gu"  # Gujarati
    ES = "es"  # Spanish


class InterpretationTier(StrEnum):
    """Depth-of-analysis tier exposed at the API.

    The model behind each tier is a deployment decision and is not
    revealed by the API. Tier labels stay stable — the model can
    rotate.
    """

    BASIC = "basic"  # ~3-5 paragraphs, fast
    STANDARD = "standard"  # ~6-10 paragraphs, balanced
    PREMIUM = "premium"  # 12-20 paragraphs, deep synthesis


class InterpretationType(StrEnum):
    """Kind of LLM interpretation produced by the API."""

    THEME = "theme"
    CHART_READING = "chart_reading"
    DASHA_FORECAST = "dasha_forecast"
    MUHURTA = "muhurta"


class AstrologySystem(StrEnum):
    """Tropical (western) vs sidereal (vedic) zodiac."""

    WESTERN = "western"
    VEDIC = "vedic"


class AyanamshaType(StrEnum):
    """Sidereal offset used by the Vedic engine.

    The server currently only accepts ``lahiri``. The resource
    signature still accepts ``AyanamshaType | str`` so callers can
    forward a future server-side variant without an SDK upgrade.
    """

    LAHIRI = "lahiri"


class HouseSystem(StrEnum):
    """House-division convention.

    Matches the server's ``Literal["placidus","whole_sign","equal"]``.
    """

    PLACIDUS = "placidus"
    WHOLE_SIGN = "whole_sign"
    EQUAL = "equal"


class UsageGroupBy(StrEnum):
    """Break-down dimension for ``GET /v1/llm/usage-summary``."""

    NONE = "none"
    INTERPRETATION_TYPE = "interpretation_type"
    TIER = "tier"
    LANGUAGE = "language"
    DAY = "day"
