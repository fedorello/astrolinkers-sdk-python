"""Enumerations used by the Vedic engine endpoints.

Server-side these are FastAPI ``Literal[...]`` types; mirroring them
as ``StrEnum`` here gives consumers IDE auto-completion and lets
``mypy --strict`` catch typos at call sites.
"""

from __future__ import annotations

from enum import StrEnum


class Varga(StrEnum):
    """Divisional chart ids supported by ``/v1/vedic/.../divisional/{varga}``."""

    D1 = "D1"
    D2 = "D2"
    D2_SUN_MOON = "D2_SUN_MOON"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"
    D6 = "D6"
    D7 = "D7"
    D8 = "D8"
    D9 = "D9"
    D10 = "D10"
    D11 = "D11"
    D12 = "D12"
    D16 = "D16"
    D20 = "D20"
    D24 = "D24"
    D27 = "D27"
    D30 = "D30"
    D40 = "D40"
    D45 = "D45"
    D60 = "D60"


class BhavaStyle(StrEnum):
    """Bhava chakra computation style."""

    RAMAN = "raman"
    EQUAL = "equal"


class VimshopakaGroup(StrEnum):
    """Varga group used for the Vimshopaka bala."""

    SHAD_VARGA = "shad_varga"
    SAPTA_VARGA = "sapta_varga"
    DASHA_VARGA = "dasha_varga"
    SHODASHA_VARGA = "shodasha_varga"


class TheoArea(StrEnum):
    """The eleven life areas of the Theo system."""

    SELF = "self"
    WEALTH = "wealth"
    SIBLINGS = "siblings"
    HOME = "home"
    CHILDREN = "children"
    HEALTH = "health"
    PARTNERSHIPS = "partnerships"
    LONGEVITY = "longevity"
    DHARMA = "dharma"
    CAREER = "career"
    LOSSES = "losses"


class HouseSignificator(StrEnum):
    """Common themes from the server's ``HouseSignificator`` enum.

    The server enum has 133 entries (the full classical significator
    catalogue). The most frequently-used ones are included here for
    auto-completion; any other value still works because the field is
    typed as ``HouseSignificator | str`` in resource signatures.
    """

    CAREER = "career"
    WEALTH = "wealth"
    MARRIAGE_FOR_MAN = "marriage_for_man"
    MARRIAGE_FOR_WOMAN = "marriage_for_woman"
    CHILDREN = "children"
    MOTHER = "mother"
    FATHER = "father"
    HEALTH = "health"
    LONGEVITY = "longevity"
    SIBLINGS = "siblings"
    EDUCATION = "education"
    HAPPINESS = "happiness"
    SPIRITUAL_LIFE = "spiritual_life"
    FOREIGN_TRAVEL = "foreign_travel"
    LITIGATION = "litigation"
