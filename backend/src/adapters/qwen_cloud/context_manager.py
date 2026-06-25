from __future__ import annotations

from src.domain.models.society import DebateTurn


class DebateContextManager:
    """Manages the shared context window across debate rounds.

    Each round: collect all debater turns, then broadcast to all agents before next round.
    """

    def __init__(self, round_cap: int) -> None:
        self._round_cap = round_cap
        self._turns: list[DebateTurn] = []

    def add_turn(self, turn: DebateTurn) -> None:
        self._turns.append(turn)

    def get_context_for_round(self, round_num: int) -> list[DebateTurn]:
        return [t for t in self._turns if t.round < round_num]

    @property
    def current_round(self) -> int:
        if not self._turns:
            return 1
        return max(t.round for t in self._turns)
