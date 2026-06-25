from __future__ import annotations

from src.domain.models.outreach import ExtractedClaim, Outreach


class TaskDecomposer:
    """Breaks an ingested Outreach into discrete, individually verifiable claims."""

    async def decompose(self, outreach: Outreach) -> list[ExtractedClaim]:
        raise NotImplementedError
