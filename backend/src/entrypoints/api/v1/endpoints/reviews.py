from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.application.ports.outbound.email import EmailSender
from src.application.ports.outbound.repository import OutreachRepository
from src.domain.models.outreach import Decision, DecisionLabel, OutreachStatus, TriageVerdict
from src.entrypoints.api.dependencies import (
    CurrentProfessorDep,
    get_email_sender,
    get_outreach_repo,
)
from src.entrypoints.api.schemas import GlobalResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])

OutreachRepoDep = Annotated[OutreachRepository, Depends(get_outreach_repo)]
EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]


class OverrideRequest(BaseModel):
    label: DecisionLabel
    rationale: str | None = None
    drafted_reply: str | None = None


class ReplyRequest(BaseModel):
    body: str


@router.get("/queue", response_model=GlobalResponse[list])
async def get_queue(
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    verdict: TriageVerdict | None = Query(default=None),
) -> GlobalResponse:
    outreaches = await outreach_repo.list_by_verdict(current_professor.id, verdict)
    return GlobalResponse(
        data=[o.model_dump(mode="json") for o in outreaches],
        message=f"{len(outreaches)} outreach(es) found",
    )


@router.get("/{outreach_id}", response_model=GlobalResponse[dict])
async def get_review_detail(
    outreach_id: UUID,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
) -> GlobalResponse:
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")
    return GlobalResponse(data=outreach.model_dump(mode="json"), message="OK")


@router.post("/{outreach_id}/approve", response_model=GlobalResponse[dict])
async def approve_decision(
    outreach_id: UUID,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
) -> GlobalResponse:
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")
    if not outreach.decision:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No decision to approve — debate has not completed",
        )
    return GlobalResponse(data=outreach.model_dump(mode="json"), message="Decision approved")


@router.post("/{outreach_id}/override", response_model=GlobalResponse[dict])
async def override_decision(
    outreach_id: UUID,
    body: OverrideRequest,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
) -> GlobalResponse:
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")
    outreach.decision = Decision(
        label=body.label,
        rationale=body.rationale or "",
        drafted_reply=body.drafted_reply,
        overridden_by_professor=True,
    )
    saved = await outreach_repo.save(outreach)
    return GlobalResponse(data=saved.model_dump(mode="json"), message="Decision overridden")


@router.post("/{outreach_id}/reply", response_model=GlobalResponse[dict])
async def send_reply(
    outreach_id: UUID,
    body: ReplyRequest,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    email_sender: EmailSenderDep,
) -> GlobalResponse:
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")

    subject = outreach.subject or "your message"
    await email_sender.send_reply(
        to_email=outreach.sender_email,
        reply_to_email=current_professor.email,  # professor's real .edu
        subject=f"Re: {subject}",
        body_text=body.body,
    )

    outreach.status = OutreachStatus.REPLIED
    outreach.replied_at = datetime.now(UTC)
    saved = await outreach_repo.save(outreach)
    return GlobalResponse(data=saved.model_dump(mode="json"), message="Reply sent")
