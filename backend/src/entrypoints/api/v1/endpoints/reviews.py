from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.application.ports.outbound.repository import OutreachRepository
from src.entrypoints.api.dependencies import get_outreach_repo
from src.entrypoints.api.schemas import GlobalResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/queue", response_model=GlobalResponse[list])
async def get_queue(
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
) -> GlobalResponse:
    raise NotImplementedError


@router.get("/{outreach_id}", response_model=GlobalResponse[dict])
async def get_review_detail(
    outreach_id: UUID,
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
) -> GlobalResponse:
    raise NotImplementedError


@router.post("/{outreach_id}/approve", response_model=GlobalResponse[dict])
async def approve_decision(
    outreach_id: UUID,
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
) -> GlobalResponse:
    raise NotImplementedError


@router.post("/{outreach_id}/override", response_model=GlobalResponse[dict])
async def override_decision(
    outreach_id: UUID,
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
) -> GlobalResponse:
    raise NotImplementedError
