from __future__ import annotations

from src.adapters.qwen_cloud.tools.capacity_math import assess_capacity, capacity_math_tool
from src.domain.models.professor import Capacity


def test_effective_slots_never_negative() -> None:
    result = assess_capacity(Capacity(open_slots=2, students_committed=5))
    assert result.effective_open_slots == 0
    assert result.at_capacity is True
    assert "no open slots" in result.note.lower()


def test_effective_slots_subtracts_committed() -> None:
    result = assess_capacity(Capacity(open_slots=5, students_committed=2))
    assert result.effective_open_slots == 3
    assert result.at_capacity is False
    assert "3 effective open slot" in result.note


def test_budget_and_funding_source_pass_through() -> None:
    result = assess_capacity(
        Capacity(
            open_slots=1, students_committed=0, budget_amount=40000, funding_source="professor"
        )
    )
    assert result.budget_amount == 40000
    assert result.funding_source == "professor"


async def test_capacity_math_tool_invokable_end_to_end() -> None:
    result = await capacity_math_tool.ainvoke(
        {"open_slots": 3, "students_committed": 1, "budget_amount": None, "funding_source": None}
    )
    assert result["effective_open_slots"] == 2
    assert result["at_capacity"] is False
