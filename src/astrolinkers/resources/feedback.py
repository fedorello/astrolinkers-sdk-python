"""Feedback resource — submit verdicts on template statements."""

from __future__ import annotations

from astrolinkers._transport import AsyncTransport, SyncTransport
from astrolinkers.types.feedback import (
    FeedbackEntry,
    FeedbackRole,
    FeedbackVerdict,
    TemplateAccuracy,
)


def _submit_body(
    *,
    statement_id: str,
    verdict: FeedbackVerdict,
    role: FeedbackRole,
    user_id: str | None,
    organization_id: str | None,
    comment: str | None,
    confidence: float | None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "statement_id": statement_id,
        "verdict": verdict,
        "role": role,
    }
    if user_id is not None:
        body["user_id"] = user_id
    if organization_id is not None:
        body["organization_id"] = organization_id
    if comment is not None:
        body["comment"] = comment
    if confidence is not None:
        body["confidence"] = confidence
    return body


class AsyncFeedback:
    """Async feedback resource."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def submit(
        self,
        *,
        statement_id: str,
        verdict: FeedbackVerdict,
        role: FeedbackRole = "subject",
        user_id: str | None = None,
        organization_id: str | None = None,
        comment: str | None = None,
        confidence: float | None = None,
    ) -> FeedbackEntry:
        """Submit feedback on a template statement."""
        data = await self._transport.request(
            "POST",
            "/v1/feedback",
            json=_submit_body(
                statement_id=statement_id,
                verdict=verdict,
                role=role,
                user_id=user_id,
                organization_id=organization_id,
                comment=comment,
                confidence=confidence,
            ),
        )
        return FeedbackEntry.model_validate(data)

    async def retrieve(self, feedback_id: str) -> FeedbackEntry:
        """Fetch a stored feedback entry."""
        data = await self._transport.request(
            "GET",
            f"/v1/feedback/{feedback_id}",
        )
        return FeedbackEntry.model_validate(data)

    async def template_accuracy(self, template_id: str) -> TemplateAccuracy:
        """Rolling accuracy aggregate for one template."""
        data = await self._transport.request(
            "GET",
            f"/v1/feedback/templates/{template_id}",
        )
        return TemplateAccuracy.model_validate(data)


class SyncFeedback:
    """Sync mirror of :class:`AsyncFeedback`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def submit(
        self,
        *,
        statement_id: str,
        verdict: FeedbackVerdict,
        role: FeedbackRole = "subject",
        user_id: str | None = None,
        organization_id: str | None = None,
        comment: str | None = None,
        confidence: float | None = None,
    ) -> FeedbackEntry:
        """Submit feedback on a template statement."""
        data = self._transport.request(
            "POST",
            "/v1/feedback",
            json=_submit_body(
                statement_id=statement_id,
                verdict=verdict,
                role=role,
                user_id=user_id,
                organization_id=organization_id,
                comment=comment,
                confidence=confidence,
            ),
        )
        return FeedbackEntry.model_validate(data)

    def retrieve(self, feedback_id: str) -> FeedbackEntry:
        """Fetch a stored feedback entry."""
        data = self._transport.request(
            "GET",
            f"/v1/feedback/{feedback_id}",
        )
        return FeedbackEntry.model_validate(data)

    def template_accuracy(self, template_id: str) -> TemplateAccuracy:
        """Rolling accuracy aggregate for one template."""
        data = self._transport.request(
            "GET",
            f"/v1/feedback/templates/{template_id}",
        )
        return TemplateAccuracy.model_validate(data)
