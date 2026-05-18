"""Settings validation."""

from __future__ import annotations

import pytest

from astrolinkers._settings import ClientSettings


def test_settings_accepts_minimum_valid_input() -> None:
    settings = ClientSettings(api_key="x")
    assert settings.api_key == "x"
    assert settings.base_url.startswith("https://")
    assert settings.timeout > 0
    assert settings.max_retries >= 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"api_key": ""},
        {"api_key": "x", "base_url": "ftp://x"},
        {"api_key": "x", "timeout": 0},
        {"api_key": "x", "timeout": -1},
        {"api_key": "x", "read_timeout": 0},
        {"api_key": "x", "max_retries": -1},
    ],
)
def test_settings_rejects_invalid_input(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ClientSettings(**kwargs)  # type: ignore[arg-type]
