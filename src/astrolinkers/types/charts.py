"""Pydantic models for charts and the data that produces them."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from astrolinkers.types.enums import AstrologySystem, AyanamshaType, HouseSystem


class BirthData(BaseModel):
    """Birth coordinates + moment used to compute a natal chart."""

    model_config = ConfigDict(frozen=True)

    moment: datetime = Field(
        ...,
        description="Birth moment as an aware UTC timestamp.",
    )
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PlanetPosition(BaseModel):
    """One planet's position in a chart."""

    model_config = ConfigDict(extra="allow")

    planet: str
    longitude: float
    sign: str
    degree_in_sign: float
    speed_per_day: float
    is_retrograde: bool
    nakshatra: str | None = None
    pada: int | None = None
    global_pada: int | None = None
    nakshatra_lord: str | None = None
    navamsa_sign: str | None = None
    navamsa_lord: str | None = None


class HouseCusp(BaseModel):
    """Ecliptic longitude of one house cusp."""

    model_config = ConfigDict(frozen=True)

    house: int = Field(..., ge=1, le=12)
    longitude: float


class Chart(BaseModel):
    """A natal chart returned by the API.

    Extra fields are tolerated so additions on the server (new index
    fields, computed extras) do not break older SDK versions.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    system: AstrologySystem
    ayanamsha: AyanamshaType | str | None = None
    house_system: HouseSystem | str
    computed_at: datetime
    birth: BirthData
    planets: list[PlanetPosition]
    houses: list[HouseCusp] = Field(default_factory=list)
