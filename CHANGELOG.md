# Changelog

All notable changes to this SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [0.2.1] — 2026-05-19

Schema-alignment release. Every typed response now matches the
canonical OpenAPI shape (`/openapi.json`), so endpoints that used to
raise `pydantic.ValidationError` on parse — `api_keys.issue`,
`api_keys.list`, `plans.list`, `plans.get_tenant_plan`,
`plans.set_tenant_plan`, `profiles.talent`, `interpretations.create`,
`reports.create`, `reports.retrieve`, `usage.api_key`,
`usage.tenant` — return correctly typed models instead.

The previous 0.2.0 surface for these endpoints never worked against
the real server, so there are no backwards-compat shims for the old
field names.

### Fixed

* **api-keys.** `IssuedApiKey` is now a flat model mirroring the
  server's `IssuedApiKeyResponse` (fields `id, name, key_prefix,
  key_last4, display, scopes, owner_tenant_id, created_at,
  created_by, last_used_at, expires_at, revoked_at, metadata,
  plaintext`). The nested `{api_key, token}` wrapper has been
  removed; the plaintext bearer is now `IssuedApiKey.plaintext`.
  `ApiKey` gained `key_prefix, key_last4, display, owner_tenant_id,
  created_by`. `api_keys.list()` now reads the response envelope's
  `keys` field instead of a non-existent `items` fallback.

* **plans.** `Plan` rewritten to match `PlanResponse`: `tier,
  display_name, monthly_price_usd, rate_limit_capacity,
  rate_limit_refill_per_second, llm_cost_cap_per_hour_usd, status,
  features`. The old `name, monthly_call_cap, metadata` fields
  are gone. `TenantPlan` rewritten as `tenant_id, display_name,
  plan: Plan, plan_updated_at, created_at` (nested catalogue entry
  under `plan`). `plans.list()` reads the response envelope's
  `plans` field.

* **profiles.** `SkillProfile` rewritten to `{chart_id, scores:
  list[SkillScore]}` matching `SkillProfileResponse`. New public
  type `SkillScore = {skill_id, value, level, contributing_rules}`.
  The old `locale, skills, strengths, risks, metadata` fields are
  gone.

* **interpretations (template-driven).** `Statement` renamed
  `text -> body` and `confidence -> score`, plus the required
  fields `kind, locale, rule_path, created_at`.
  `TemplateInterpretation` dropped the spurious `metadata` and
  top-level `created_at` (server response carries neither).

* **reports.** `Report` dropped the required `locale, tone,
  metadata` fields (the server response carries none). Added
  `artifact_key` (nullable). `updated_at` is now required (server
  always sends it).

* **charts.** `HouseCusp.house_number` renamed to `house`.
  `PlanetPosition` gained `sign, degree_in_sign, navamsa_sign,
  navamsa_lord`; `speed_per_day` and `is_retrograde` are required
  (server always sends them). `Chart.metadata` removed.
  `BirthData` dropped `timezone, location_name` (the server's
  `_BirthRequest` does not accept them). The request builder in
  `charts.create` no longer sends those fields.

* **enums.** `HouseSystem.KOCH` removed (server accepts only
  `placidus | whole_sign | equal`). `AyanamshaType` reduced to
  `LAHIRI` only (server `Literal["lahiri"] | None`). The
  `charts.create` signature still accepts `AyanamshaType | str` so
  callers can forward a future variant.

* **charts.create.** Default `house_system` changed from
  `WHOLE_SIGN` to `PLACIDUS` to match the server default.

* **usage.** `HourlyUsageBucket` rewritten to match
  `UsageBucketResponse`: `bucket_hour, requests, errors_4xx,
  errors_5xx, latency_p95_ms`. The old `hour, request_count,
  success_count, error_count, last_request_at` fields are gone.
  `HourlyUsage` rewritten to match `UsageRangeResponse`: `since,
  until, total_requests, total_errors, buckets`.

* **llm.** `LLMInterpretation.interpretation_type` widened from
  `InterpretationType` to `InterpretationType | str` so new
  server-side variants do not raise `ValidationError` on parse.

## [0.2.0] — full API coverage + PyPI distribution name

This release completes the API surface — every public endpoint of
the Astrolinkers API now has a typed SDK method — and is the first
release published to PyPI.

### Changed

* **PyPI distribution name is now `astrolinkers-sdk`** (was
  `astrolinkers`). The import name is unchanged — user code still
  reads `from astrolinkers import Astrolinkers`. The brand-suffixed
  distribution name makes "this is an SDK" obvious on PyPI search
  and matches the GitHub repo (`astrolinkers-sdk-python`).
  Install with `pip install astrolinkers-sdk`.

### Added

* **`client.api_keys`** — issue / list / revoke your own bearer tokens.
* **`client.compatibility`** — synastry + ashtakoota reports between
  two charts.
* **`client.feedback`** — submit verdicts on template statements,
  read back stored feedback, query rolling template accuracy.
* **`client.health`** — `healthz` / `readyz` / `version`.
* **`client.plans`** — list catalogue, read + switch the tenant plan.
* **`client.profiles`** — talent / hiring profile from a chart.
* **`client.reports`** — enqueue + poll PDF / HTML report generation.
* **`client.usage`** — hourly API-call buckets per key and per tenant.
* **`client.vedic`** — every one of the 58 `/v1/vedic/...` engine
  endpoints (divisional charts, dasha chains, ashtakavarga, shadbala,
  panchanga, yogas, sambandhas, predictive engine, KP, muhurta, ...).
  Methods are typed with `Varga`, `TheoArea`, `HouseSignificator`,
  `BhavaStyle`, `VimshopakaGroup` enums so IDE autocomplete works for
  every parameter; response bodies stay as `dict[str, Any]` (with a
  runtime `isinstance` guard) since modelling each deep nested
  structure would create more maintenance burden than DX.

* **Escape hatch** `client.request(method, path, ...)` and
  `client.stream(method, path, ...)` for ad-hoc calls to endpoints
  the SDK does not yet wrap. Same retry / error mapping as the
  resource methods.

* `Statement`, `TemplateInterpretation`, `ApiKey`, `IssuedApiKey`,
  `CompatibilityReport`, `FeedbackEntry`, `TemplateAccuracy`,
  `Plan`, `TenantPlan`, `SkillProfile`, `Report`, `HourlyUsage`,
  `HourlyUsageBucket` Pydantic models.

* `Varga`, `BhavaStyle`, `VimshopakaGroup`, `TheoArea`,
  `HouseSignificator` enums in `astrolinkers.types.vedic_enums`.

### Changed

* **Breaking.** `client.interpretations` now wraps the *template-
  driven* `POST /v1/interpretations` flow (with statements + locale +
  tone). The previous `client.interpretations.list / retrieve /
  usage_summary` methods (which hit `/v1/llm/...`) moved onto
  `client.llm` as `list_stored / retrieve_stored / usage_summary`.
  This aligns the SDK resource names with the API URL structure.

### Quality gates

* mypy `--strict` on 42 source files — zero issues.
* ruff lint + format clean.
* 59 unit tests, all green.

## [0.1.0] — initial release

* Sync (`Astrolinkers`) and async (`AsyncAstrolinkers`) clients.
* Resources: `charts`, `llm` (4 sync + 4 stream endpoints + persist
  list / read / usage summary), `interpretations` (stored LLM
  records).
* Typed error hierarchy.
* Streaming surface built on `httpx-sse` yielding typed events
  (`MetaEvent` / `DeltaEvent` / `DoneEvent` / `ErrorEvent`).
* Retry + jittered exponential backoff; honours `Retry-After` on 429.
* Pydantic v2 models for all request / response shapes.
