from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.application.ports.outbound.repository import OutreachRepository
from src.entrypoints.api.dependencies import get_outreach_repo
from src.entrypoints.api.schemas import GlobalResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class InboundEmailPayload(BaseModel):
    sender_email: str
    sender_name: str | None = None
    body: str
    attachment_keys: list[str] = []
    received_at: datetime | None = None


@router.post("/email-intake", response_model=GlobalResponse[dict])
async def email_intake(
    payload: InboundEmailPayload,
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
) -> GlobalResponse:
    raise NotImplementedError
