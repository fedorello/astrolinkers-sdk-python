# Astrolinkers Python SDK — convenience targets.
#
# All targets use ``uv`` because that's the only package manager
# blessed in CODING_PRINCIPLES.md.

.PHONY: help test unit e2e lint type check

help:
	@echo "Targets:"
	@echo "  make unit   — run the mocked unit test suite"
	@echo "  make e2e    — run the live staging e2e smoke suite"
	@echo "  make test   — alias for 'unit'"
	@echo "  make lint   — ruff check + format check"
	@echo "  make type   — mypy --strict"
	@echo "  make check  — lint + type + unit"

test: unit

unit:
	uv run pytest tests --ignore=tests/e2e -v

# Run the live e2e suite against api.astrolinkers.com.
# Picks up the founder JWT from ~/.astrolinkers/token_founder.jwt
# automatically; override with ASTROLINKERS_E2E_TOKEN if desired.
e2e:
	ASTROLINKERS_E2E_TOKEN="$${ASTROLINKERS_E2E_TOKEN:-$$(cat ~/.astrolinkers/token_founder.jwt 2>/dev/null)}" \
		uv run pytest tests/e2e -v

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

type:
	uv run mypy --strict

check: lint type unit
