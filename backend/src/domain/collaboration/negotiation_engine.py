from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.domain.models.outreach import Decision, Outreach
from src.domain.models.professor import Professor
from src.domain.models.society import DebateTrace


class DebateOutcome(BaseModel):
    """What a completed debate produces: the full replayable trace plus the
    Arbitrator's decision (kept separate — the decision lands on the Outreach,
    the trace is persisted on its own for the replay surface)."""

    trace: DebateTrace
    decision: Decision


class NegotiationEngine(ABC):
    """Contract for the multi-round simultaneous debate (ChatEval/MAD pattern).

    This is a debate/agent society, NOT task collaboration: every debater holds
    an opinion on the SAME matter (this candidate) and sees the others' opinions
    each round to rebut or concede — as opposed to a supervisor assigning each
    agent a distinct sub-task and merging results. Debaters run in parallel each
    round; all see all prior turns before the next round; an agent with nothing
    new to add may pass. Terminates at the round cap (or earlier if every
    debater passes), then the Arbitrator resolves — it judges once at the end
    and never routes mid-debate.

    Implementations live in adapters (the orchestration framework is an infra
    concern); this contract depends only on domain models.
    """

    def __init__(self, round_cap: int) -> None:
        self.round_cap = round_cap

    @abstractmethod
    async def run(self, outreach: Outreach, professor: Professor) -> DebateOutcome:
        raise NotImplementedError
