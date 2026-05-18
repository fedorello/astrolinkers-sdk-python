"""Template-driven interpretations.

This resource wraps ``POST /v1/interpretations`` and
``GET /v1/interpretations/{id}`` — the *template-driven* interpretation
flow (with structured statements you can feed back into the
:mod:`astrolinkers.resources.feedback` accuracy loop).

This is **not** the LLM-generated interpretation flow — that one
lives on :class:`astrolinkers.resources.llm.AsyncLLM`
(``list_stored`` / ``retrieve_stored`` / ``usage_summary``). Keep
the distinction in mind: template interpretations come with a
``locale`` + ``tone`` knob, no token spend, no LLM round-trip; LLM
interpretations come with a ``language`` + ``tier`` knob and bill
for tokens.
"""

from __future__ import annotations

from typing import Literal

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.template_interpretations import TemplateInterpretation

# Stable across the API as of v1; matches the FastAPI ``Literal``s.
Locale = Literal["en", "hi", "ru"]
Tone = Literal["corporate", "coach", "vedic_traditional", "plain"]


def _create_body(
    *,
    chart_id: str,
    locale: Locale,
    tone: Tone,
    use_llm_rewrite: bool,
) -> dict[str, object]:
    """Render the request body the server expects."""
    return {
        "chart_id": chart_id,
        "locale": locale,
        "tone": tone,
        "use_llm_rewrite": use_llm_rewrite,
    }


class AsyncInterpretations:
    """Async template-driven interpretations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        chart_id: str,
        locale: Locale = "en",
        tone: Tone = "corporate",
        use_llm_rewrite: bool = False,
    ) -> TemplateInterpretation:
        """Generate a template-driven interpretation for ``chart_id``."""
        data = await self._transport.request(
            "POST",
            "/v1/interpretations",
            json=_create_body(
                chart_id=chart_id,
                locale=locale,
                tone=tone,
                use_llm_rewrite=use_llm_rewrite,
            ),
        )
        return TemplateInterpretation.model_validate(data)

    async def retrieve(self, interpretation_id: str) -> TemplateInterpretation:
        """Fetch a previously generated template interpretation."""
        data = await self._transport.request(
            "GET",
            f"/v1/interpretations/{interpretation_id}",
        )
        return TemplateInterpretation.model_validate(data)


class SyncInterpretations:
    """Sync mirror of :class:`AsyncInterpretations`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        chart_id: str,
        locale: Locale = "en",
        tone: Tone = "corporate",
        use_llm_rewrite: bool = False,
    ) -> TemplateInterpretation:
        """Generate a template-driven interpretation for ``chart_id``."""
        data = self._transport.request(
            "POST",
            "/v1/interpretations",
            json=_create_body(
                chart_id=chart_id,
                locale=locale,
                tone=tone,
                use_llm_rewrite=use_llm_rewrite,
            ),
        )
        return TemplateInterpretation.model_validate(data)

    def retrieve(self, interpretation_id: str) -> TemplateInterpretation:
        """Fetch a previously generated template interpretation."""
        data = self._transport.request(
            "GET",
            f"/v1/interpretations/{interpretation_id}",
        )
        return TemplateInterpretation.model_validate(data)
