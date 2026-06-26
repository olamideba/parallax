from __future__ import annotations

from fastapi import APIRouter

from src.entrypoints.api.dependencies import CurrentProfessorDep
from src.entrypoints.api.schemas import GlobalResponse

router = APIRouter(prefix="/professors", tags=["professors"])


@router.get("/me", response_model=GlobalResponse[dict])
async def get_me(current_professor: CurrentProfessorDep) -> GlobalResponse:
    from src.adapters.storage.models import ProfessorRecord
    import json

    p: ProfessorRecord = current_professor
    return GlobalResponse(
        data={
            "id": str(p.id),
            "email": p.email,
            "display_name": p.display_name,
            "open_slots": p.open_slots,
            "students_committed": p.students_committed,
            "budget_context": p.budget_context,
            "recruiting_topics": json.loads(p.recruiting_topics),
            "gatekeeper_aggressiveness": p.gatekeeper_aggressiveness,
        },
        message="OK",
    )
