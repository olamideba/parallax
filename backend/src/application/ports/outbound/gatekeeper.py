from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from src.domain.models.outreach import ExtractedProfile, TriageVerdict


class GatekeeperAssessment(BaseModel):
    """The Gatekeeper's cheap first-pass read of an outreach.

    Doubles as the LLM structured-output schema and the port return type.
    Claims are extracted as plain statements only — truth is the debate's job,
    so no verification happens here.
    """

    verdict: TriageVerdict
    reason: str = Field(description="One sentence justifying the verdict.")
    profile: ExtractedProfile = Field(default_factory=ExtractedProfile)
    claim_texts: list[str] = Field(
        default_factory=list,
        description="Concrete, verifiable claims the candidate makes about themselves.",
    )


class Gatekeeper(ABC):
    """Cheap triage pass over one inbound outreach (spam/irrelevant vs. worth a debate)."""

    @abstractmethod
    async def assess(
        self,
        *,
        sender_email: str,
        subject: str | None,
        body: str,
        cv_text: str | None,
        professor_topics: list[str],
        custom_instructions: str | None,
        aggressiveness: float,
    ) -> GatekeeperAssessment:
        raise NotImplementedError
