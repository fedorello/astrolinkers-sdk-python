"""Single source of truth for the SDK version.

Read at runtime to populate the ``User-Agent`` header so server-side
logs can correlate failures with a specific client version.
"""

from __future__ import annotations

# Keep in sync with ``pyproject.toml``. When releasing, bump both.
__version__ = "0.1.0"
