"""End-to-end smoke tests for the Astrolinkers Python SDK.

These tests hit the real staging API at ``https://api.astrolinkers.com``
and verify every public resource end-to-end. They are skipped unless
``ASTROLINKERS_E2E_TOKEN`` is set in the environment (typically the
founder JWT read from ``~/.astrolinkers/token_founder.jwt``).
"""
