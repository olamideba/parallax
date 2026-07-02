from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel

from src.domain.models.professor import Capacity


class CapacityAssessment(BaseModel):
    effective_open_slots: int
    at_capacity: bool
    budget_amount: int | None
    funding_source: str | None
    note: str


def assess_capacity(capacity: Capacity) -> CapacityAssessment:
    """Deterministic arithmetic over declared capacity (SKILL: capacity-math).

    No LLM call — see skills/capacity_math/SKILL.md for the documented
    procedure this implements.
    """
    effective = max(0, capacity.open_slots - capacity.students_committed)
    note = (
        "No open slots — do not represent there is room for another student."
        if effective == 0
        else f"{effective} effective open slot(s)."
    )
    return CapacityAssessment(
        effective_open_slots=effective,
        at_capacity=effective == 0,
        budget_amount=capacity.budget_amount,
        funding_source=capacity.funding_source,
        note=note,
    )


@tool
def capacity_math_tool(
    open_slots: int,
    students_committed: int,
    budget_amount: int | None = None,
    funding_source: str | None = None,
) -> dict:
    """Compute the professor's effective open capacity deterministically. Use
    this whenever reasoning about whether there's room for another student —
    never estimate or eyeball this yourself."""
    capacity = Capacity(
        open_slots=open_slots,
        students_committed=students_committed,
        budget_amount=budget_amount,
        funding_source=funding_source,
    )
    return assess_capacity(capacity).model_dump()
