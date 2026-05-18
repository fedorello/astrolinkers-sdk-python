# Astrolinkers Python SDK

Official Python client for the [Astrolinkers API](https://astrolinkers.com) —
natal charts, talent profiles, Vedic calculations, and engine-grounded LLM
interpretations.

* **Sync + async** clients (`Astrolinkers` / `AsyncAstrolinkers`).
* **Typed everything** — Pydantic v2 models, `py.typed` marker, mypy strict.
* **Streaming** of LLM interpretations as a typed iterator of events.
* **Retry-aware** — honours `Retry-After`, exponential backoff with jitter
  on transient failures.
* **Multilingual** — English plus 8 Indian languages + Spanish out of the box.

> Status: alpha (`0.1.0`). Public API may shift between minor releases until
> `1.0`. Pin the minor version when integrating.

---

## Install

```bash
pip install astrolinkers
# or with uv
uv add astrolinkers
```

Requires Python 3.12+.

## Quickstart

```python
from datetime import datetime, UTC
from astrolinkers import Astrolinkers, InterpretationTier, Language

client = Astrolinkers(api_key="alk_live_…")

# 1. Compute a natal chart.
chart = client.charts.create(
    moment=datetime(1990, 4, 15, 2, 0, tzinfo=UTC),
    latitude=28.6139, longitude=77.2090,
    timezone="Asia/Kolkata",
    location_name="New Delhi, India",
)

# 2. Ask the LLM for a per-life-area interpretation.
career = client.llm.theme(
    chart_id=chart.id,
    theme="career",
    language=Language.EN,
    tier=InterpretationTier.STANDARD,
)
print(career.content)

# 3. Full-chart reading at premium depth.
reading = client.llm.chart_reading(
    chart_id=chart.id,
    language=Language.HI,            # Hindi (Devanagari script)
    tier=InterpretationTier.PREMIUM,
)
print(reading.cost_usd, reading.cached)
```

## Streaming

Every LLM endpoint has a `*_stream` sibling that yields typed events as the
model produces tokens. The first event is `MetaEvent` carrying the engine
context — render it immediately so users see grounded numbers before any
LLM text arrives.

```python
from astrolinkers import Astrolinkers, MetaEvent, DeltaEvent, DoneEvent

client = Astrolinkers(api_key="alk_live_…")

for event in client.llm.chart_reading_stream(chart_id=chart.id, tier="standard"):
    match event:
        case MetaEvent():
            ui.render_engine_blocks(event.engine_context)
        case DeltaEvent():
            ui.append_text(event.content)
        case DoneEvent():
            ui.show_cost(event.cost_usd, cached=event.cached)
```

Async usage is identical — `async for event in client.llm.chart_reading_stream(...)`.

## Re-reading past interpretations

Every successful LLM call is persisted server-side. List and read past
interpretations without re-billing:

```python
page = client.interpretations.list(chart_id=chart.id, limit=20)
for row in page.items:
    print(row.id, row.interpretation_type, row.cost_usd, row.created_at)

# Fetch one back later.
row = client.interpretations.retrieve(page.items[0].id)
print(row.content)
```

## Usage analytics

```python
from datetime import datetime, UTC, timedelta
from astrolinkers import UsageGroupBy

today = datetime.now(UTC)
summary = client.interpretations.usage_summary(
    from_=today - timedelta(days=30),
    to=today,
    group_by=UsageGroupBy.TIER,
)
print(f"30-day spend: ${summary.total.cost_usd:.4f}")
for bucket in summary.breakdown:
    print(f"  {bucket.label}: {bucket.call_count} calls, ${bucket.cost_usd:.4f}")
```

## Error handling

```python
from astrolinkers import (
    Astrolinkers,
    RateLimitedError, AuthenticationError, BudgetExceededError,
    NotFoundError, ServerError,
)

try:
    reading = client.llm.chart_reading(chart_id="bogus", tier="premium")
except NotFoundError:
    ...
except RateLimitedError as e:
    print(f"Slow down for {e.retry_after_seconds:.0f}s")
except BudgetExceededError as e:
    print(f"Budget hit: ${e.spent_usd:.2f} of ${e.cap_usd:.2f}")
except AuthenticationError:
    ...
except ServerError:
    ...  # The SDK already retried; this is a real outage.
```

## Async usage

```python
import asyncio
from astrolinkers import AsyncAstrolinkers

async def main():
    async with AsyncAstrolinkers(api_key="alk_live_…") as client:
        chart = await client.charts.create(...)
        reading = await client.llm.chart_reading(chart_id=chart.id)
        print(reading.content)

asyncio.run(main())
```

## Configuration

| Argument            | Default                       | Notes                                                            |
|---------------------|-------------------------------|------------------------------------------------------------------|
| `api_key`           | —                             | Required. Bearer token issued by Astrolinkers.                   |
| `base_url`          | `https://api.astrolinkers.com`| Override for staging / self-hosted.                              |
| `timeout`           | 60s                           | Connect / write timeout.                                         |
| `read_timeout`      | 300s                          | Long for premium streams. `None` disables.                       |
| `max_retries`       | 2                             | Transient 5xx / connection errors. 429 honours `Retry-After`.    |
| `user_agent_suffix` | —                             | Appended to `User-Agent` for server-side correlation.            |

## Versioning

Semantic versioning. Until `1.0` breaking changes may land on minors; pin
your minor (`astrolinkers~=0.1`) and bump deliberately.

## License

MIT — see [LICENSE](LICENSE).
