"""End-to-end smoke test for the Astrolinkers Python SDK.

Runs against the live staging API. The goal is wide coverage rather
than deep semantic assertions — every public resource is exercised at
least once so any drift between SDK and server fails loudly.

To run::

    ASTROLINKERS_E2E_TOKEN=$(cat ~/.astrolinkers/token_founder.jwt) \\
        uv run pytest tests/e2e/ -v

The whole module skips cleanly if neither ``ASTROLINKERS_E2E_TOKEN``
nor ``~/.astrolinkers/token_founder.jwt`` is present.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from astrolinkers import (
    Astrolinkers,
    AstrologySystem,
    AsyncAstrolinkers,
    Chart,
    CompatibilityReport,
    DoneEvent,
    ErrorEvent,
    FeedbackEntry,
    HouseSignificator,
    HouseSystem,
    InterpretationTier,
    IssuedApiKey,
    Language,
    LLMInterpretation,
    MetaEvent,
    Plan,
    Report,
    SkillProfile,
    Statement,
    StoredLLMInterpretation,
    TemplateAccuracy,
    TemplateInterpretation,
    TenantPlan,
    TheoArea,
    UsageGroupBy,
    UsageSummary,
    Varga,
)
from astrolinkers.types.api_keys import ApiKey
from astrolinkers.types.usage_buckets import HourlyUsage

# ----------------------------------------------------------------------------
# Module-level skip
# ----------------------------------------------------------------------------

_FOUNDER_PATH = Path.home() / ".astrolinkers" / "token_founder.jwt"
_TOKEN_AVAILABLE = bool(os.environ.get("ASTROLINKERS_E2E_TOKEN")) or _FOUNDER_PATH.exists()

pytestmark = pytest.mark.skipif(
    not _TOKEN_AVAILABLE,
    reason=(
        "e2e smoke requires ASTROLINKERS_E2E_TOKEN env var or "
        "~/.astrolinkers/token_founder.jwt"
    ),
)


# ----------------------------------------------------------------------------
# Common constants — chosen to match the chart fixtures in conftest.
# ----------------------------------------------------------------------------

# Reference "now" pinned for the duration of one test run. Using
# ``datetime.now(UTC)`` once at import time keeps usage / dasha / transit
# queries deterministic and lets retries reuse the same query window.
NOW: datetime = datetime.now(tz=UTC)
ONE_DAY = timedelta(days=1)

# Birth-day-derived defaults used by Vedic endpoints that take query
# moments. Keeping them tied to the chart fixture means the response
# is predictable.
SUNRISE_DEFAULT: datetime = datetime(1990, 4, 15, 0, 0, tzinfo=UTC)
EVENT_DATE_DEFAULT: datetime = datetime(2020, 1, 1, 0, 0, tzinfo=UTC)


# ----------------------------------------------------------------------------
# Health resource
# ----------------------------------------------------------------------------


def test_health_endpoints(sync_client: Astrolinkers) -> None:
    """``/healthz``, ``/readyz``, ``/version`` all reachable and JSON."""
    health = sync_client.health.healthz()
    assert isinstance(health, dict)

    ready = sync_client.health.readyz()
    assert isinstance(ready, dict)

    version = sync_client.health.version()
    assert isinstance(version, dict)


# ----------------------------------------------------------------------------
# Charts resource
# ----------------------------------------------------------------------------


def test_chart_create_and_round_trip(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Chart fixture is the create path; round-trip via retrieve."""
    fetched = sync_client.charts.retrieve(chart_a.id)
    assert fetched.id == chart_a.id
    assert fetched.system == AstrologySystem.VEDIC
    # House cusps should be populated for a real chart.
    assert chart_a.houses, "chart should expose houses"
    assert chart_a.houses[0].house >= 1


# ----------------------------------------------------------------------------
# Profiles resource
# ----------------------------------------------------------------------------


def test_profiles_talent(sync_client: Astrolinkers, chart_a: Chart) -> None:
    """Talent profile returns SkillProfile with at least one scored skill."""
    profile = sync_client.profiles.talent(chart_a.id)
    assert isinstance(profile, SkillProfile)
    assert profile.chart_id == chart_a.id
    assert profile.scores, "profile should have at least one skill score"
    first = profile.scores[0]
    assert first.skill_id
    assert isinstance(first.value, float)


# ----------------------------------------------------------------------------
# Template-driven interpretations + feedback
# ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def template_interpretation(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> TemplateInterpretation:
    """Module-scoped template interpretation used by interpretations + feedback."""
    return sync_client.interpretations.create(
        chart_id=chart_a.id,
        locale="en",
        tone="corporate",
    )


def test_interpretations_create_and_retrieve(
    sync_client: Astrolinkers,
    template_interpretation: TemplateInterpretation,
) -> None:
    """Statements come back with body + score; retrieve round-trips."""
    interp = template_interpretation
    assert isinstance(interp, TemplateInterpretation)
    assert interp.statements, "interpretation should have at least one statement"
    first = interp.statements[0]
    assert isinstance(first, Statement)
    assert first.body
    assert isinstance(first.score, float)

    fetched = sync_client.interpretations.retrieve(interp.id)
    assert fetched.id == interp.id


def test_feedback_submit_retrieve_and_template_accuracy(
    sync_client: Astrolinkers,
    template_interpretation: TemplateInterpretation,
) -> None:
    """Submit feedback on the first statement; round-trip; check accuracy."""
    statement = template_interpretation.statements[0]
    # The SDK exposes FeedbackVerdict = Literal["correct", "doubtful", "wrong"]
    # — the task brief mentioned ``"accurate"`` but the server rejects it
    # (HTTP 422). Use the canonical enum value the SDK + server agree on.
    entry = sync_client.feedback.submit(
        statement_id=statement.id,
        verdict="correct",
    )
    assert isinstance(entry, FeedbackEntry)
    assert entry.statement_id == statement.id

    fetched = sync_client.feedback.retrieve(entry.id)
    assert fetched.id == entry.id

    accuracy = sync_client.feedback.template_accuracy(statement.template_id)
    assert isinstance(accuracy, TemplateAccuracy)
    assert accuracy.template_id == statement.template_id


# ----------------------------------------------------------------------------
# Compatibility resource
# ----------------------------------------------------------------------------


def test_compatibility_talent_axis(
    sync_client: Astrolinkers,
    chart_a: Chart,
    chart_b: Chart,
) -> None:
    """Talent-axis compatibility report has overall score + nested kuta."""
    report = sync_client.compatibility.create(
        chart_a_id=chart_a.id,
        chart_b_id=chart_b.id,
        axis="talent",
    )
    assert isinstance(report, CompatibilityReport)
    assert isinstance(report.overall_score_percent, float)
    assert 0.0 <= report.overall_score_percent <= 100.0

    fetched = sync_client.compatibility.retrieve(report.id)
    assert fetched.id == report.id


def test_compatibility_romantic_axis(
    sync_client: Astrolinkers,
    chart_a: Chart,
    chart_b: Chart,
) -> None:
    """Romantic-axis compatibility report parses too."""
    report = sync_client.compatibility.create(
        chart_a_id=chart_a.id,
        chart_b_id=chart_b.id,
        axis="romantic",
    )
    assert report.axis == "romantic"


# ----------------------------------------------------------------------------
# Reports resource
# ----------------------------------------------------------------------------


def test_reports_create_and_retrieve(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Reports come back as typed Report with status='pending' or 'running'."""
    report = sync_client.reports.create(
        chart_id=chart_a.id,
        kind="talent_lens",
        format="html",
    )
    assert isinstance(report, Report)
    assert report.chart_id == chart_a.id
    # Don't poll forever — just verify one retrieve works.
    fetched = sync_client.reports.retrieve(report.id)
    assert fetched.id == report.id
    assert fetched.status in {"pending", "running", "ready", "failed"}


# ----------------------------------------------------------------------------
# LLM resource — sync POST + stream siblings
# ----------------------------------------------------------------------------


def test_llm_chart_reading_sync(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Full chart-reading at the STANDARD tier returns typed content."""
    reading = sync_client.llm.chart_reading(
        chart_id=chart_a.id,
        language=Language.EN,
        tier=InterpretationTier.STANDARD,
    )
    assert isinstance(reading, LLMInterpretation)
    assert reading.content
    assert reading.tier == InterpretationTier.STANDARD


def test_llm_theme_sync(sync_client: Astrolinkers, chart_a: Chart) -> None:
    """Theme interpretation for ``career``."""
    out = sync_client.llm.theme(
        chart_id=chart_a.id,
        theme="career",
        language=Language.EN,
        tier=InterpretationTier.STANDARD,
    )
    assert out.content


def test_llm_dasha_forecast_sync(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Dasha forecast at the pinned NOW moment."""
    out = sync_client.llm.dasha_forecast(
        chart_id=chart_a.id,
        at=NOW,
        language=Language.EN,
        tier=InterpretationTier.STANDARD,
    )
    assert out.content


def test_llm_muhurta_reasoning_sync(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Muhurta reasoning over a short 6-hour window."""
    out = sync_client.llm.muhurta_reasoning(
        chart_id=chart_a.id,
        window_start=NOW,
        window_end=NOW + timedelta(hours=6),
        language=Language.EN,
        tier=InterpretationTier.STANDARD,
        interval_minutes=60,
        top_n=3,
    )
    assert out.content


def _drain_sync_stream(
    factory: Callable[[], object],
) -> tuple[list[MetaEvent], list[DoneEvent], list[ErrorEvent]]:
    """Drain an SDK sync stream and bucket events by type.

    Accepts a no-arg factory so this helper can wrap each ``*_stream``
    method without needing to know its keyword arguments.
    """
    metas: list[MetaEvent] = []
    dones: list[DoneEvent] = []
    errors: list[ErrorEvent] = []
    stream = factory()
    # mypy doesn't know it's iterable without an explicit cast — but
    # all ``*_stream`` SDK returns implement ``Iterator``.
    for event in stream:  # type: ignore[attr-defined]
        if isinstance(event, MetaEvent):
            metas.append(event)
        elif isinstance(event, DoneEvent):
            dones.append(event)
        elif isinstance(event, ErrorEvent):
            errors.append(event)
    return metas, dones, errors


def test_llm_chart_reading_stream(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """At least one Meta and one terminal event from the stream."""
    metas, dones, errors = _drain_sync_stream(
        lambda: sync_client.llm.chart_reading_stream(
            chart_id=chart_a.id,
            tier=InterpretationTier.STANDARD,
        ),
    )
    assert metas, "chart_reading_stream should yield a meta event"
    assert dones or errors, "stream should terminate with done or error"


def test_llm_theme_stream(sync_client: Astrolinkers, chart_a: Chart) -> None:
    """Theme stream terminates with at least one meta + terminal event."""
    metas, dones, errors = _drain_sync_stream(
        lambda: sync_client.llm.theme_stream(
            chart_id=chart_a.id,
            theme="career",
            tier=InterpretationTier.STANDARD,
        ),
    )
    assert metas
    assert dones or errors


def test_llm_dasha_forecast_stream(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Dasha forecast stream meta + terminal event."""
    metas, dones, errors = _drain_sync_stream(
        lambda: sync_client.llm.dasha_forecast_stream(
            chart_id=chart_a.id,
            at=NOW,
            tier=InterpretationTier.STANDARD,
        ),
    )
    assert metas
    assert dones or errors


def test_llm_muhurta_reasoning_stream(
    sync_client: Astrolinkers,
    chart_a: Chart,
) -> None:
    """Muhurta reasoning stream meta + terminal event."""
    metas, dones, errors = _drain_sync_stream(
        lambda: sync_client.llm.muhurta_reasoning_stream(
            chart_id=chart_a.id,
            window_start=NOW,
            window_end=NOW + timedelta(hours=6),
            tier=InterpretationTier.STANDARD,
            interval_minutes=60,
            top_n=3,
        ),
    )
    assert metas
    assert dones or errors


def test_llm_list_stored(sync_client: Astrolinkers, chart_a: Chart) -> None:
    """List stored LLM interpretations — should include at least one."""
    page = sync_client.llm.list_stored(chart_id=chart_a.id, limit=10)
    assert isinstance(page.items, list)
    assert page.limit == 10


def test_llm_retrieve_stored(sync_client: Astrolinkers, chart_a: Chart) -> None:
    """Retrieve the first stored interpretation; if none exist, skip."""
    page = sync_client.llm.list_stored(chart_id=chart_a.id, limit=1)
    if not page.items:
        pytest.skip("no stored interpretations to retrieve")
    fetched = sync_client.llm.retrieve_stored(page.items[0].id)
    assert isinstance(fetched, StoredLLMInterpretation)
    assert fetched.id == page.items[0].id


def test_llm_usage_summary(sync_client: Astrolinkers) -> None:
    """Usage summary grouped by tier returns a typed total bucket."""
    summary = sync_client.llm.usage_summary(
        from_=NOW - ONE_DAY,
        to=NOW,
        group_by=UsageGroupBy.TIER,
    )
    assert isinstance(summary, UsageSummary)
    assert isinstance(summary.total.cost_usd, float)


# ----------------------------------------------------------------------------
# Plans + tenant plan
# ----------------------------------------------------------------------------


def test_plans_list(sync_client: Astrolinkers) -> None:
    """Plan catalogue lists at least one plan."""
    plans = sync_client.plans.list()
    assert plans, "plans.list() returned empty"
    assert isinstance(plans[0], Plan)


def test_plans_get_tenant_plan(sync_client: Astrolinkers) -> None:
    """Tenant plan resolves and carries a nested Plan."""
    tenant_plan = sync_client.plans.get_tenant_plan()
    assert isinstance(tenant_plan, TenantPlan)
    assert isinstance(tenant_plan.plan, Plan)


# ----------------------------------------------------------------------------
# Usage (raw API hits) + API keys
# ----------------------------------------------------------------------------


def test_usage_api_key(
    sync_client: Astrolinkers,
    issued_test_key: IssuedApiKey,
) -> None:
    """Per-key usage range."""
    usage = sync_client.usage.api_key(
        issued_test_key.id,
        since=NOW - ONE_DAY,
        until=NOW,
    )
    assert isinstance(usage, HourlyUsage)


def test_usage_tenant(sync_client: Astrolinkers) -> None:
    """Tenant-wide usage range."""
    usage = sync_client.usage.tenant(since=NOW - ONE_DAY, until=NOW)
    assert isinstance(usage, HourlyUsage)


def test_api_keys_list_contains_issued_key(
    sync_client: Astrolinkers,
    issued_test_key: IssuedApiKey,
) -> None:
    """The freshly issued key shows up in the list."""
    keys = sync_client.api_keys.list()
    ids = {k.id for k in keys}
    assert issued_test_key.id in ids
    assert all(isinstance(k, ApiKey) for k in keys)


# ----------------------------------------------------------------------------
# Vedic resource — exhaustive sweep
# ----------------------------------------------------------------------------
#
# Each helper in this section invokes one specific Vedic method with
# sensible defaults, returning the result so the caller can assert.
# We do not introspect ``client.vedic`` reflectively because that would
# strip type information; instead each method is called by name (typed
# at the call site) and the per-method test fails loudly with the
# method name in the report when the SDK ↔ API contract drifts.


def test_vedic_divisional(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.divisional(chart_a.id, Varga.D9)
    assert isinstance(out, dict)


def test_vedic_bhava_chakra(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.bhava_chakra(chart_a.id), dict)


def test_vedic_special_lagnas(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.special_lagnas(chart_a.id), dict)


def test_vedic_aspects(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.aspects(chart_a.id), dict)


def test_vedic_aspects_with_orb(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.aspects_with_orb(chart_a.id), dict)


def test_vedic_dignity(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.dignity(chart_a.id), dict)


def test_vedic_functional_nature(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.functional_nature(chart_a.id), dict)


def test_vedic_vimshottari(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.vimshottari(chart_a.id), dict)


def test_vedic_current_dasha(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.current_dasha(chart_a.id, at=NOW), dict)


def test_vedic_yogini_dasha(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.yogini_dasha(chart_a.id), dict)


def test_vedic_chara_dasha(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.chara_dasha(chart_a.id), dict)


def test_vedic_period_lords(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.period_lords(chart_a.id, sunrise=SUNRISE_DEFAULT)
    assert isinstance(out, dict)


def test_vedic_yogas(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.yogas(chart_a.id), dict)


def test_vedic_jaimini_karakas(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.jaimini_karakas(chart_a.id), dict)


def test_vedic_arudha(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.arudha(chart_a.id), dict)


def test_vedic_badhaka(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.badhaka(chart_a.id), dict)


def test_vedic_ashtakavarga(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.ashtakavarga(chart_a.id), dict)


def test_vedic_ashtakavarga_corrected(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.ashtakavarga_corrected(chart_a.id), dict)


def test_vedic_panchanga(sync_client: Astrolinkers) -> None:
    """Panchanga — moment + place, no chart id."""
    out = sync_client.vedic.panchanga(at=NOW, lat=28.6139, lon=77.2090)
    assert isinstance(out, dict)


def test_vedic_shadbala(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.shadbala(chart_a.id), dict)


def test_vedic_shadbala_kala(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.shadbala_kala(chart_a.id), dict)


def test_vedic_shadbala_kala_full(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.shadbala_kala_full(chart_a.id), dict)


def test_vedic_composite_strength(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.composite_strength(chart_a.id), dict)


def test_vedic_sign_strengths(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.sign_strengths(chart_a.id), dict)


def test_vedic_house_strengths(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.house_strengths(chart_a.id), dict)


def test_vedic_bhava_bala(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.bhava_bala(chart_a.id), dict)


def test_vedic_ishta_kashta(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.ishta_kashta(chart_a.id), dict)


def test_vedic_vimshopaka(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.vimshopaka(chart_a.id, "sun"), dict)


def test_vedic_varga_dignity(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.varga_dignity(chart_a.id), dict)


def test_vedic_sambandhas(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.sambandhas(chart_a.id, p1="sun", p2="moon")
    assert isinstance(out, dict)


def test_vedic_sambandhas_for_planet(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    assert isinstance(sync_client.vedic.sambandhas_for_planet(chart_a.id, "sun"), dict)


def test_vedic_extended_sambandhas(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    out = sync_client.vedic.extended_sambandhas(chart_a.id, p1="sun", p2="moon")
    assert isinstance(out, dict)


def test_vedic_extended_sambandhas_for_planet(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    out = sync_client.vedic.extended_sambandhas_for_planet(chart_a.id, "sun")
    assert isinstance(out, dict)


def test_vedic_house_relations_for_planet(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    out = sync_client.vedic.house_relations_for_planet(chart_a.id, "sun")
    assert isinstance(out, dict)


def test_vedic_house_relations_for_house(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    out = sync_client.vedic.house_relations_for_house(chart_a.id, 1)
    assert isinstance(out, dict)


def test_vedic_special_vargas(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.special_vargas(chart_a.id), dict)


def test_vedic_corrected_nature(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.corrected_nature(chart_a.id), dict)


def test_vedic_rays(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.rays(chart_a.id), dict)


def test_vedic_progression(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.progression(chart_a.id, event_date=EVENT_DATE_DEFAULT)
    assert isinstance(out, dict)


def test_vedic_influence_network(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.influence_network(chart_a.id), dict)


def test_vedic_rectify_lagna(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.rectify_lagna(chart_a.id), dict)


def test_vedic_theo_house_roles(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.theo_house_roles(chart_a.id, 1), dict)


def test_vedic_theo_sign_influences(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    assert isinstance(sync_client.vedic.theo_sign_influences(chart_a.id), dict)


def test_vedic_theo_thematic(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.theo_thematic(chart_a.id, TheoArea.CAREER)
    assert isinstance(out, dict)


def test_vedic_house_quality(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.house_quality(chart_a.id), dict)


def test_vedic_materialization(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.materialization(chart_a.id, TheoArea.CAREER)
    assert isinstance(out, dict)


def test_vedic_materialization_at(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.materialization_at(
        chart_a.id, TheoArea.CAREER, at=NOW,
    )
    assert isinstance(out, dict)


def test_vedic_essential_planets(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.essential_planets(chart_a.id, HouseSignificator.CAREER)
    assert isinstance(out, dict)


def test_vedic_period_modifiers(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.period_modifiers(chart_a.id, at=NOW), dict)


def test_vedic_transit_modifiers(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.transit_modifiers(chart_a.id, at=NOW), dict)


def test_vedic_transit_contacts(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.transit_contacts(chart_a.id, at=NOW), dict)


def test_vedic_transit_navamsa_activations(
    sync_client: Astrolinkers, chart_a: Chart,
) -> None:
    out = sync_client.vedic.transit_navamsa_activations(chart_a.id, at=NOW)
    assert isinstance(out, dict)


def test_vedic_probability(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.probability(
        chart_a.id, HouseSignificator.CAREER, at=NOW,
    )
    assert isinstance(out, dict)


def test_vedic_complete_factor(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.complete_factor(chart_a.id, HouseSignificator.CAREER)
    assert isinstance(out, dict)


def test_vedic_meta_factors(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.meta_factors(chart_a.id), dict)


def test_vedic_varshaphala(sync_client: Astrolinkers, chart_a: Chart) -> None:
    assert isinstance(sync_client.vedic.varshaphala(chart_a.id, 30), dict)


def test_vedic_kp_lookup(sync_client: Astrolinkers) -> None:
    """KP lookup — chartless, just a longitude."""
    assert isinstance(sync_client.vedic.kp_lookup(longitude_deg=123.456), dict)


def test_vedic_muhurta(sync_client: Astrolinkers, chart_a: Chart) -> None:
    out = sync_client.vedic.muhurta(
        chart_a.id,
        window_start=NOW,
        window_end=NOW + timedelta(hours=6),
        interval_minutes=60,
        top_n=3,
    )
    assert isinstance(out, dict)


# ----------------------------------------------------------------------------
# Async client — representative coverage only (sync covers the surface)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_async_charts_create_and_round_trip(
    async_client: AsyncAstrolinkers,
) -> None:
    """Async charts create + retrieve."""
    chart = await async_client.charts.create(
        moment=datetime(1985, 6, 21, 12, 0, tzinfo=UTC),
        latitude=40.7128,
        longitude=-74.0060,
        system="vedic",
        house_system=HouseSystem.PLACIDUS,
    )
    fetched = await async_client.charts.retrieve(chart.id)
    assert fetched.id == chart.id


@pytest.mark.asyncio(loop_scope="session")
async def test_async_profiles_talent(
    async_client: AsyncAstrolinkers,
    chart_a: Chart,
) -> None:
    """Async profile fetch on the shared sync-created chart."""
    profile = await async_client.profiles.talent(chart_a.id)
    assert profile.chart_id == chart_a.id


@pytest.mark.asyncio(loop_scope="session")
async def test_async_llm_chart_reading(
    async_client: AsyncAstrolinkers,
    chart_a: Chart,
) -> None:
    """Async non-streaming LLM."""
    out = await async_client.llm.chart_reading(
        chart_id=chart_a.id,
        tier=InterpretationTier.STANDARD,
    )
    assert out.content


@pytest.mark.asyncio(loop_scope="session")
async def test_async_vedic_divisional(
    async_client: AsyncAstrolinkers,
    chart_a: Chart,
) -> None:
    """One representative Vedic call via the async transport."""
    out = await async_client.vedic.divisional(chart_a.id, Varga.D9)
    assert isinstance(out, dict)


@pytest.mark.asyncio(loop_scope="session")
async def test_async_plans_list(async_client: AsyncAstrolinkers) -> None:
    """Async plans listing."""
    plans = await async_client.plans.list()
    assert plans
    assert isinstance(plans[0], Plan)
