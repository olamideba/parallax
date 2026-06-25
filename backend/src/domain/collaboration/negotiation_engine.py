from __future__ import annotations

from uuid import UUID

from src.domain.models.outreach import Outreach
from src.domain.models.society import DebateTrace


class NegotiationEngine:
    """Orchestrates multi-round simultaneous debate (ChatEval/MAD pattern).

    Debaters run in parallel each round; all see all responses before the next round.
    Terminates at round cap or when the Arbitrator calls it.
    """

    def __init__(self, round_cap: int) -> None:
        self.round_cap = round_cap

    async def run(self, outreach: Outreach, professor_id: UUID) -> DebateTrace:
        raise NotImplementedError
