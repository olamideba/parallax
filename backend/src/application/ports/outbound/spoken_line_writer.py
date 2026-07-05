from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models.society import AgentRole


class SpokenLineWriter(ABC):
    """Rewrites a debate turn's full evidentiary text into a short, conversational
    line meant to be *spoken* (for TTS), not read.

    The debate itself never produces this — `content` stays the complete record
    (receipts, citations, the auditor's full findings). The spoken line is a
    lossy, speech-shaped rendering generated after the fact, used only to drive
    the replay's audio.
    """

    @abstractmethod
    async def to_spoken_line(self, role: AgentRole, content: str) -> str:
        raise NotImplementedError
