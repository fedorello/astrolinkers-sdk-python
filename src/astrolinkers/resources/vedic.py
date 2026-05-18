"""Vedic engine — all 58 ``/v1/vedic/...`` endpoints.

Every method returns a ``dict[str, Any]`` because Vedic responses
are deeply nested, structured JSON (divisional chart maps, dasha
chains, sambandha graphs, ashtakavarga matrices) and modelling each
one would be more maintenance burden than DX benefit — consumers
iterate / index these structures rather than match against a model.

Method signatures *are* typed, so IDE auto-completion works at the
call site and ``mypy --strict`` catches typos in path / query
parameters. The :mod:`astrolinkers.types.vedic_enums` module exposes
``Varga``, ``TheoArea``, ``HouseSignificator``, etc. for the same
reason.

If a future caller needs typed access to a specific response, they
can either build their own Pydantic model and validate the dict,
or open a PR extending this module with a typed return shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.vedic_enums import (
    BhavaStyle,
    HouseSignificator,
    TheoArea,
    Varga,
    VimshopakaGroup,
)


def _ensure_dict(value: Any) -> dict[str, Any]:
    """Runtime guard — the transport returns the raw decoded JSON.

    Every Vedic endpoint contracts to return a JSON object; this
    helper turns a violation (e.g. a server change that returns a
    list or a null) into a loud :class:`TypeError` at the call site
    instead of letting a wrong type leak into user code.
    """
    if not isinstance(value, dict):
        raise TypeError(
            f"Expected JSON object from Vedic endpoint, got {type(value).__name__}",
        )
    return value


def _at_params(at: datetime) -> dict[str, object]:
    """Common single-moment query: ``?at=<iso>``."""
    return {"at": at.isoformat()}


def _muhurta_params(
    *,
    window_start: datetime,
    window_end: datetime,
    interval_minutes: int,
    top_n: int,
) -> dict[str, object]:
    return {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "interval_minutes": interval_minutes,
        "top_n": top_n,
    }


# ─────────────────────────────────────────────────────────────────
# Async resource
# ─────────────────────────────────────────────────────────────────


class AsyncVedic:
    """Async access to every ``/v1/vedic/...`` endpoint."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    # ── Divisional + bhava ───────────────────────────────────────

    async def divisional(
        self,
        chart_id: str,
        varga: Varga,
    ) -> dict[str, Any]:
        """Planet→sign map in a divisional chart (D1 .. D60)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/divisional/{varga.value}",
            )
        )

    async def bhava_chakra(
        self,
        chart_id: str,
        *,
        style: BhavaStyle = BhavaStyle.RAMAN,
    ) -> dict[str, Any]:
        """Bhava (house) chakra in Raman or Equal style."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/bhava-chakra",
                params={"style": style},
            )
        )

    async def special_lagnas(self, chart_id: str) -> dict[str, Any]:
        """Bhava / Hora / Ghatika lagnas."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/special-lagnas",
            )
        )

    async def aspects(self, chart_id: str) -> dict[str, Any]:
        """Vedic drishti — regular Parashara + special aspects."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/aspects",
            )
        )

    async def aspects_with_orb(self, chart_id: str) -> dict[str, Any]:
        """Continuous orb-modulated aspect strength."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/aspects/with-orb",
            )
        )

    async def dignity(self, chart_id: str) -> dict[str, Any]:
        """Per-planet dignity (Exalt / Mooltrikona / Own / ... / Debilitation)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dignity",
            )
        )

    async def functional_nature(self, chart_id: str) -> dict[str, Any]:
        """Functional nature of each planet for the chart's ascendant."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/functional-nature",
            )
        )

    # ── Dasha + period lords ─────────────────────────────────────

    async def vimshottari(self, chart_id: str) -> dict[str, Any]:
        """Full Vimshottari MD / AD / PD chain from natal Moon."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/vimshottari",
            )
        )

    async def current_dasha(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Current Vimshottari MD / AD / PD at a moment."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/current",
                params=_at_params(at),
            )
        )

    async def yogini_dasha(
        self,
        chart_id: str,
        *,
        total_years: int = 72,
    ) -> dict[str, Any]:
        """Yogini dasha — 8-yogini, 36-year cycle from janma nakshatra."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/yogini",
                params={"total_years": total_years},
            )
        )

    async def chara_dasha(
        self,
        chart_id: str,
        *,
        total_years: int = 78,
    ) -> dict[str, Any]:
        """Chara (Jaimini) dasha — sign-based, lord-position years."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/chara",
                params={"total_years": total_years},
            )
        )

    async def period_lords(
        self,
        chart_id: str,
        *,
        sunrise: datetime,
    ) -> dict[str, Any]:
        """Year / month / day / hora classical period lords."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/period-lords",
                params={"sunrise": sunrise.isoformat()},
            )
        )

    # ── Yogas, karakas, arudhas, badhaka ─────────────────────────

    async def yogas(self, chart_id: str) -> dict[str, Any]:
        """Detected yogas (Raja, Pancha Mahapurusha, Gajakesari, ...)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/yogas",
            )
        )

    async def jaimini_karakas(self, chart_id: str) -> dict[str, Any]:
        """7 Jaimini karakas (Atma .. Daraka) by descending degree."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/karakas/jaimini",
            )
        )

    async def arudha(self, chart_id: str) -> dict[str, Any]:
        """Arudha pada for every house."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/arudha",
            )
        )

    async def badhaka(self, chart_id: str) -> dict[str, Any]:
        """Badhaka sign + lord for the chart's lagna."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/badhaka",
            )
        )

    # ── Ashtakavarga ─────────────────────────────────────────────

    async def ashtakavarga(self, chart_id: str) -> dict[str, Any]:
        """Full Ashtakavarga: 7 Bhinnashtakas + Sarvashtaka."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ashtakavarga",
            )
        )

    async def ashtakavarga_corrected(self, chart_id: str) -> dict[str, Any]:
        """Corrected Bhinnashtaka (Trikona + Ekadhipatya Shodhana)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ashtakavarga/corrected",
            )
        )

    # ── Panchanga / location-bound ───────────────────────────────

    async def panchanga(
        self,
        *,
        at: datetime,
        lat: float,
        lon: float,
    ) -> dict[str, Any]:
        """Full panchanga (5 angas + muhurtas + kalams) for a moment + place."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                "/v1/vedic/panchanga",
                params={"at": at.isoformat(), "lat": lat, "lon": lon},
            )
        )

    # ── Shadbala + strengths ─────────────────────────────────────

    async def shadbala(self, chart_id: str) -> dict[str, Any]:
        """Shadbala — simplified port (4 of 6 balas implemented)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala",
            )
        )

    async def shadbala_kala(self, chart_id: str) -> dict[str, Any]:
        """Kala bala sub-balas (paksha + vara + abda + masa + yuddha)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala/kala",
            )
        )

    async def shadbala_kala_full(self, chart_id: str) -> dict[str, Any]:
        """Ephemeris-time Kala bala — Natha + Unnatha + Tribhaga + Ayana."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala/kala-full",
            )
        )

    async def composite_strength(self, chart_id: str) -> dict[str, Any]:
        """Composite per-planet strength (shadbala + vimshopaka + dignity)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/composite",
            )
        )

    async def sign_strengths(self, chart_id: str) -> dict[str, Any]:
        """Composite strength score for each zodiac sign."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/signs",
            )
        )

    async def house_strengths(self, chart_id: str) -> dict[str, Any]:
        """Composite strength score for each of the 12 houses."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/houses",
            )
        )

    async def bhava_bala(self, chart_id: str) -> dict[str, Any]:
        """Bhava bala per house (bhavadhipati + dig + drishti)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/bhava-bala",
            )
        )

    async def ishta_kashta(self, chart_id: str) -> dict[str, Any]:
        """Ishta (beneficial) and Kashta (harmful) phala per planet."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ishta-kashta",
            )
        )

    async def vimshopaka(
        self,
        chart_id: str,
        planet: str,
        *,
        group: VimshopakaGroup = VimshopakaGroup.SHAD_VARGA,
    ) -> dict[str, Any]:
        """Vimshopaka bala 0..20 for a planet in a varga group."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/vimshopaka/{planet}",
                params={"group": group},
            )
        )

    async def varga_dignity(self, chart_id: str) -> dict[str, Any]:
        """Own-sign hit count across the Shodasha-varga group per planet."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/varga-dignity",
            )
        )

    # ── Sambandhas ───────────────────────────────────────────────

    async def sambandhas(
        self,
        chart_id: str,
        *,
        p1: str,
        p2: str,
    ) -> dict[str, Any]:
        """Base sambandhas (5 sub-types) between two planets."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/sambandhas",
                params={"p1": p1, "p2": p2},
            )
        )

    async def sambandhas_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """All sambandhas affecting one planet, with total Virupa strength."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/sambandhas/{planet}",
            )
        )

    async def extended_sambandhas(
        self,
        chart_id: str,
        *,
        p1: str,
        p2: str,
    ) -> dict[str, Any]:
        """Extended sambandhas (9 sub-types) between two planets."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/extended-sambandhas",
                params={"p1": p1, "p2": p2},
            )
        )

    async def extended_sambandhas_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """All extended sambandhas affecting one planet."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/extended-sambandhas/{planet}",
            )
        )

    # ── House relations + special vargas ─────────────────────────

    async def house_relations_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """Every relation between one planet and the 12 houses."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-relations/planet/{planet}",
            )
        )

    async def house_relations_for_house(
        self,
        chart_id: str,
        house_number: int,
    ) -> dict[str, Any]:
        """Every relation linking any planet to one house."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-relations/house/{house_number}",
            )
        )

    async def special_vargas(self, chart_id: str) -> dict[str, Any]:
        """22nd drekkana from Lagna + 64th navamsa from Moon (death vargas)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/special-vargas",
            )
        )

    async def corrected_nature(self, chart_id: str) -> dict[str, Any]:
        """Mercury contamination + Moon phase nature corrections."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/corrected-nature",
            )
        )

    # ── Rays + rectification + Theo ──────────────────────────────

    async def rays(self, chart_id: str) -> dict[str, Any]:
        """7-Rays classification — per-planet ray count and total."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/rays",
            )
        )

    async def progression(
        self,
        chart_id: str,
        *,
        event_date: datetime,
    ) -> dict[str, Any]:
        """Age-based planetary progression to an event date."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/progression",
                params={"event_date": event_date.isoformat()},
            )
        )

    async def influence_network(self, chart_id: str) -> dict[str, Any]:
        """Theo influence network — signed influences on planets + houses."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/influence-network",
            )
        )

    async def rectify_lagna(
        self,
        chart_id: str,
        *,
        step_minutes: int = 10,
    ) -> dict[str, Any]:
        """Kunda-Siddhanta lagna rectification (Janma-Tara matching)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/rectify-lagna",
                params={"step_minutes": step_minutes},
            )
        )

    async def theo_house_roles(
        self,
        chart_id: str,
        house_number: int,
    ) -> dict[str, Any]:
        """Role each planet plays relative to a target house."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/house-roles/{house_number}",
            )
        )

    async def theo_sign_influences(self, chart_id: str) -> dict[str, Any]:
        """Per-sign net benefic/malefic influence (occupants + aspectors)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/sign-influences",
            )
        )

    async def theo_thematic(
        self,
        chart_id: str,
        area: TheoArea,
    ) -> dict[str, Any]:
        """Houses + karakas + activated planets for one life area."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/thematic/{area.value}",
            )
        )

    async def house_quality(self, chart_id: str) -> dict[str, Any]:
        """Per-house auspiciousness (VERY_DIFFICULT .. VERY_GOOD)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-quality",
            )
        )

    # ── Predictive ───────────────────────────────────────────────

    async def materialization(
        self,
        chart_id: str,
        area: TheoArea,
    ) -> dict[str, Any]:
        """Natal base potential (0..1) for a life area."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/predict/materialization/{area.value}",
            )
        )

    async def materialization_at(
        self,
        chart_id: str,
        area: TheoArea,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Date-bound materialization probability — natal x transit modifier."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/predict/materialization/{area.value}/at",
                params=_at_params(at),
            )
        )

    async def essential_planets(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
    ) -> dict[str, Any]:
        """Planets most responsible for one life theme."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/essential-planets/{theme_value}",
            )
        )

    async def period_modifiers(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Per-planet quality modifier under the dasha chain at a moment."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/period-modifiers",
                params=_at_params(at),
            )
        )

    async def transit_modifiers(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Per-planet transit-quality modifier (SAV + Bhinnashtaka at transit)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transit-modifiers",
                params=_at_params(at),
            )
        )

    async def transit_contacts(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Transit-vs-natal aspect / conjunction contacts at a moment."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transits/contacts",
                params=_at_params(at),
            )
        )

    async def transit_navamsa_activations(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Transiting planets sharing a D9 sign with natal planets."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transits/navamsa-activations",
                params=_at_params(at),
            )
        )

    async def probability(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
        *,
        at: datetime | None = None,
    ) -> dict[str, Any]:
        """Full theme probability — 7-source decomposition w/ smooth decrease."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        params: dict[str, object] = {}
        if at is not None:
            params["at"] = at.isoformat()
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/probability/{theme_value}",
                params=params or None,
            )
        )

    async def complete_factor(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
    ) -> dict[str, Any]:
        """Complete factor — full structured explanation of one theme's probability."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/complete-factor/{theme_value}",
            )
        )

    async def meta_factors(self, chart_id: str) -> dict[str, Any]:
        """Meta factors — planets driving multiple themes across the chart."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/meta-factors",
            )
        )

    # ── KP, varshaphala, muhurta ─────────────────────────────────

    async def varshaphala(
        self,
        chart_id: str,
        age_years: int,
    ) -> dict[str, Any]:
        """Varshaphala — annual chart for a specific age (Muntha + solar return)."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/varshaphala/{age_years}",
            )
        )

    async def kp_lookup(self, *, longitude_deg: float) -> dict[str, Any]:
        """KP sub-lord lookup for an arbitrary longitude."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                "/v1/vedic/kp/lookup",
                params={"longitude_deg": longitude_deg},
            )
        )

    async def muhurta(
        self,
        chart_id: str,
        *,
        window_start: datetime,
        window_end: datetime,
        interval_minutes: int = 60,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Muhurta optimizer — rank candidate moments by tara + day-lord."""
        return _ensure_dict(
            await self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/muhurta",
                params=_muhurta_params(
                    window_start=window_start,
                    window_end=window_end,
                    interval_minutes=interval_minutes,
                    top_n=top_n,
                ),
            )
        )


# ─────────────────────────────────────────────────────────────────
# Sync resource
# ─────────────────────────────────────────────────────────────────


class SyncVedic:
    """Sync mirror of :class:`AsyncVedic`.

    Every method has the same signature; ``await`` is dropped at the
    call site.
    """

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def divisional(self, chart_id: str, varga: Varga) -> dict[str, Any]:
        """Planet→sign map in a divisional chart (D1 .. D60)."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/divisional/{varga.value}",
            )
        )

    def bhava_chakra(
        self,
        chart_id: str,
        *,
        style: BhavaStyle = BhavaStyle.RAMAN,
    ) -> dict[str, Any]:
        """Bhava (house) chakra in Raman or Equal style."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/bhava-chakra",
                params={"style": style},
            )
        )

    def special_lagnas(self, chart_id: str) -> dict[str, Any]:
        """Bhava / Hora / Ghatika lagnas."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/special-lagnas",
            )
        )

    def aspects(self, chart_id: str) -> dict[str, Any]:
        """Vedic drishti — regular Parashara + special aspects."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/aspects",
            )
        )

    def aspects_with_orb(self, chart_id: str) -> dict[str, Any]:
        """Continuous orb-modulated aspect strength."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/aspects/with-orb",
            )
        )

    def dignity(self, chart_id: str) -> dict[str, Any]:
        """Per-planet dignity."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dignity",
            )
        )

    def functional_nature(self, chart_id: str) -> dict[str, Any]:
        """Functional nature of each planet for the chart's ascendant."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/functional-nature",
            )
        )

    def vimshottari(self, chart_id: str) -> dict[str, Any]:
        """Full Vimshottari MD / AD / PD chain from natal Moon."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/vimshottari",
            )
        )

    def current_dasha(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Current Vimshottari MD / AD / PD at a moment."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/current",
                params=_at_params(at),
            )
        )

    def yogini_dasha(
        self,
        chart_id: str,
        *,
        total_years: int = 72,
    ) -> dict[str, Any]:
        """Yogini dasha — 8-yogini, 36-year cycle."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/yogini",
                params={"total_years": total_years},
            )
        )

    def chara_dasha(
        self,
        chart_id: str,
        *,
        total_years: int = 78,
    ) -> dict[str, Any]:
        """Chara (Jaimini) dasha — sign-based."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/dasha/chara",
                params={"total_years": total_years},
            )
        )

    def period_lords(
        self,
        chart_id: str,
        *,
        sunrise: datetime,
    ) -> dict[str, Any]:
        """Year / month / day / hora classical period lords."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/period-lords",
                params={"sunrise": sunrise.isoformat()},
            )
        )

    def yogas(self, chart_id: str) -> dict[str, Any]:
        """Detected yogas."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/yogas",
            )
        )

    def jaimini_karakas(self, chart_id: str) -> dict[str, Any]:
        """7 Jaimini karakas by descending degree."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/karakas/jaimini",
            )
        )

    def arudha(self, chart_id: str) -> dict[str, Any]:
        """Arudha pada for every house."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/arudha",
            )
        )

    def badhaka(self, chart_id: str) -> dict[str, Any]:
        """Badhaka sign + lord for the chart's lagna."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/badhaka",
            )
        )

    def ashtakavarga(self, chart_id: str) -> dict[str, Any]:
        """Full Ashtakavarga."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ashtakavarga",
            )
        )

    def ashtakavarga_corrected(self, chart_id: str) -> dict[str, Any]:
        """Corrected Bhinnashtaka."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ashtakavarga/corrected",
            )
        )

    def panchanga(
        self,
        *,
        at: datetime,
        lat: float,
        lon: float,
    ) -> dict[str, Any]:
        """Full panchanga for a moment + place."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                "/v1/vedic/panchanga",
                params={"at": at.isoformat(), "lat": lat, "lon": lon},
            )
        )

    def shadbala(self, chart_id: str) -> dict[str, Any]:
        """Shadbala — simplified port."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala",
            )
        )

    def shadbala_kala(self, chart_id: str) -> dict[str, Any]:
        """Kala bala sub-balas."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala/kala",
            )
        )

    def shadbala_kala_full(self, chart_id: str) -> dict[str, Any]:
        """Ephemeris-time Kala bala."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/shadbala/kala-full",
            )
        )

    def composite_strength(self, chart_id: str) -> dict[str, Any]:
        """Composite per-planet strength."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/composite",
            )
        )

    def sign_strengths(self, chart_id: str) -> dict[str, Any]:
        """Composite strength score for each zodiac sign."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/signs",
            )
        )

    def house_strengths(self, chart_id: str) -> dict[str, Any]:
        """Composite strength score for each of the 12 houses."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/strength/houses",
            )
        )

    def bhava_bala(self, chart_id: str) -> dict[str, Any]:
        """Bhava bala per house."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/bhava-bala",
            )
        )

    def ishta_kashta(self, chart_id: str) -> dict[str, Any]:
        """Ishta and Kashta phala per planet."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/ishta-kashta",
            )
        )

    def vimshopaka(
        self,
        chart_id: str,
        planet: str,
        *,
        group: VimshopakaGroup = VimshopakaGroup.SHAD_VARGA,
    ) -> dict[str, Any]:
        """Vimshopaka bala 0..20 for a planet in a varga group."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/vimshopaka/{planet}",
                params={"group": group},
            )
        )

    def varga_dignity(self, chart_id: str) -> dict[str, Any]:
        """Own-sign hit count across the Shodasha-varga group."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/varga-dignity",
            )
        )

    def sambandhas(
        self,
        chart_id: str,
        *,
        p1: str,
        p2: str,
    ) -> dict[str, Any]:
        """Base sambandhas (5 sub-types) between two planets."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/sambandhas",
                params={"p1": p1, "p2": p2},
            )
        )

    def sambandhas_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """All sambandhas affecting one planet."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/sambandhas/{planet}",
            )
        )

    def extended_sambandhas(
        self,
        chart_id: str,
        *,
        p1: str,
        p2: str,
    ) -> dict[str, Any]:
        """Extended sambandhas (9 sub-types) between two planets."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/extended-sambandhas",
                params={"p1": p1, "p2": p2},
            )
        )

    def extended_sambandhas_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """All extended sambandhas affecting one planet."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/extended-sambandhas/{planet}",
            )
        )

    def house_relations_for_planet(
        self,
        chart_id: str,
        planet: str,
    ) -> dict[str, Any]:
        """Every relation between one planet and the 12 houses."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-relations/planet/{planet}",
            )
        )

    def house_relations_for_house(
        self,
        chart_id: str,
        house_number: int,
    ) -> dict[str, Any]:
        """Every relation linking any planet to one house."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-relations/house/{house_number}",
            )
        )

    def special_vargas(self, chart_id: str) -> dict[str, Any]:
        """22nd drekkana + 64th navamsa (death vargas)."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/special-vargas",
            )
        )

    def corrected_nature(self, chart_id: str) -> dict[str, Any]:
        """Mercury contamination + Moon phase nature corrections."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/corrected-nature",
            )
        )

    def rays(self, chart_id: str) -> dict[str, Any]:
        """7-Rays classification."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/rays",
            )
        )

    def progression(
        self,
        chart_id: str,
        *,
        event_date: datetime,
    ) -> dict[str, Any]:
        """Age-based planetary progression to an event date."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/progression",
                params={"event_date": event_date.isoformat()},
            )
        )

    def influence_network(self, chart_id: str) -> dict[str, Any]:
        """Theo influence network."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/influence-network",
            )
        )

    def rectify_lagna(
        self,
        chart_id: str,
        *,
        step_minutes: int = 10,
    ) -> dict[str, Any]:
        """Kunda-Siddhanta lagna rectification."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/rectify-lagna",
                params={"step_minutes": step_minutes},
            )
        )

    def theo_house_roles(
        self,
        chart_id: str,
        house_number: int,
    ) -> dict[str, Any]:
        """Role each planet plays relative to a target house."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/house-roles/{house_number}",
            )
        )

    def theo_sign_influences(self, chart_id: str) -> dict[str, Any]:
        """Per-sign net benefic/malefic influence."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/sign-influences",
            )
        )

    def theo_thematic(
        self,
        chart_id: str,
        area: TheoArea,
    ) -> dict[str, Any]:
        """Houses + karakas + activated planets for one life area."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/theo/thematic/{area.value}",
            )
        )

    def house_quality(self, chart_id: str) -> dict[str, Any]:
        """Per-house auspiciousness."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/house-quality",
            )
        )

    def materialization(
        self,
        chart_id: str,
        area: TheoArea,
    ) -> dict[str, Any]:
        """Natal base potential (0..1) for a life area."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/predict/materialization/{area.value}",
            )
        )

    def materialization_at(
        self,
        chart_id: str,
        area: TheoArea,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Date-bound materialization probability."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/predict/materialization/{area.value}/at",
                params=_at_params(at),
            )
        )

    def essential_planets(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
    ) -> dict[str, Any]:
        """Planets most responsible for one life theme."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/essential-planets/{theme_value}",
            )
        )

    def period_modifiers(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Per-planet quality modifier under the dasha chain."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/period-modifiers",
                params=_at_params(at),
            )
        )

    def transit_modifiers(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Per-planet transit-quality modifier."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transit-modifiers",
                params=_at_params(at),
            )
        )

    def transit_contacts(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Transit-vs-natal contacts at a moment."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transits/contacts",
                params=_at_params(at),
            )
        )

    def transit_navamsa_activations(
        self,
        chart_id: str,
        *,
        at: datetime,
    ) -> dict[str, Any]:
        """Transiting planets sharing a D9 sign with natal planets."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/transits/navamsa-activations",
                params=_at_params(at),
            )
        )

    def probability(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
        *,
        at: datetime | None = None,
    ) -> dict[str, Any]:
        """Full theme probability — 7-source decomposition."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        params: dict[str, object] = {}
        if at is not None:
            params["at"] = at.isoformat()
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/probability/{theme_value}",
                params=params or None,
            )
        )

    def complete_factor(
        self,
        chart_id: str,
        theme: HouseSignificator | str,
    ) -> dict[str, Any]:
        """Complete factor for one theme's probability."""
        theme_value = theme.value if isinstance(theme, HouseSignificator) else theme
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/complete-factor/{theme_value}",
            )
        )

    def meta_factors(self, chart_id: str) -> dict[str, Any]:
        """Meta factors — planets driving multiple themes."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/meta-factors",
            )
        )

    def varshaphala(
        self,
        chart_id: str,
        age_years: int,
    ) -> dict[str, Any]:
        """Varshaphala — annual chart for a specific age."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/varshaphala/{age_years}",
            )
        )

    def kp_lookup(self, *, longitude_deg: float) -> dict[str, Any]:
        """KP sub-lord lookup for an arbitrary longitude."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                "/v1/vedic/kp/lookup",
                params={"longitude_deg": longitude_deg},
            )
        )

    def muhurta(
        self,
        chart_id: str,
        *,
        window_start: datetime,
        window_end: datetime,
        interval_minutes: int = 60,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Muhurta optimizer — rank candidate moments."""
        return _ensure_dict(
            self._transport.request(
                "GET",
                f"/v1/vedic/charts/{chart_id}/muhurta",
                params=_muhurta_params(
                    window_start=window_start,
                    window_end=window_end,
                    interval_minutes=interval_minutes,
                    top_n=top_n,
                ),
            )
        )
