# Changelog

All notable changes to this SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial release. Sync (`Astrolinkers`) and async (`AsyncAstrolinkers`)
  clients with resource-based API:

  * `client.charts` — create / fetch natal charts.
  * `client.llm` — engine-grounded LLM interpretations (theme,
    chart-reading, dasha-forecast, muhurta-reasoning) in sync and
    streaming variants; persisted store list / read; usage summary
    analytics.
  * `client.interpretations` — list and read previously persisted
    interpretations.

- Typed error hierarchy: `AstrolinkersError` →
  `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
  `InvalidRequestError`, `RateLimitedError`, `BudgetExceededError`,
  `ServerError`, `ConnectionError`, `TimeoutError`.

- Streaming surface: `client.llm.theme_stream(...)` and the three
  sibling methods yield typed events (`MetaEvent`, `DeltaEvent`,
  `DoneEvent`, `ErrorEvent`) — built on `httpx-sse`.

- Automatic retry with exponential backoff for transient failures
  (5xx, connection errors) and honours `Retry-After` on 429.

- Pydantic v2 models for all request / response shapes.
