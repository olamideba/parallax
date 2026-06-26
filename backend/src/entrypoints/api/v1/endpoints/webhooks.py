from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from uuid6 import uuid7

from src.application.ports.outbound.repository import OutreachRepository
from src.domain.models.outreach import Outreach
from src.entrypoints.api.dependencies import get_outreach_repo
from src.entrypoints.api.schemas import GlobalResponse
from src.entrypoints.workers.intake_consumer import triage_and_ingest
from src.config import get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

OutreachRepoDep = Annotated[OutreachRepository, Depends(get_outreach_repo)]


class InboundEmailPayload(BaseModel):
    professor_id: UUID
    sender_email: str
    sender_name: str | None = None
    body: str
    attachment_keys: list[str] = []
    received_at: datetime | None = None


@router.post("/email-intake", response_model=GlobalResponse[dict], status_code=status.HTTP_202_ACCEPTED)
async def email_intake(
    payload: InboundEmailPayload,
    outreach_repo: OutreachRepoDep,
    x_intake_secret: Annotated[str | None, Header(alias="X-Intake-Secret")] = None,
) -> GlobalResponse:
    settings = get_settings()
    if settings.INTAKE_WEBHOOK_SECRET and x_intake_secret != settings.INTAKE_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")

    outreach = Outreach(
        id=uuid7(),
        professor_id=payload.professor_id,
        channel="email",
        sender_email=payload.sender_email,
        sender_name=payload.sender_name,
        body=payload.body,
        attachment_keys=payload.attachment_keys,
        received_at=payload.received_at or datetime.now(timezone.utc),
    )
    saved = await outreach_repo.save(outreach)
    triage_and_ingest.delay(str(saved.id), str(saved.professor_id))
    return GlobalResponse(
        data={"outreach_id": str(saved.id)},
        message="Intake queued for processing",
    )
