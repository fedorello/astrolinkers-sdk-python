# Changelog

All notable changes to this SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] — full API coverage

This release completes the API surface — every public endpoint of
the Astrolinkers API now has a typed SDK method.

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
