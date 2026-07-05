from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel

from src.application.ports.outbound.email import EmailSender
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
)
from src.domain.exceptions.base import NotFoundError
from src.domain.models.outreach import (
    SYSTEM_CONFIRMATION_CHANNEL,
    Decision,
    DecisionLabel,
    OutreachStatus,
    TriageVerdict,
)
from src.entrypoints.api.dependencies import (
    CurrentProfessorDep,
    get_email_sender,
    get_object_storage,
    get_outreach_repo,
    get_trace_repo,
)
from src.entrypoints.api.schemas import GlobalResponse
from src.entrypoints.workers.intake_consumer import triage_and_ingest

router = APIRouter(prefix="/reviews", tags=["reviews"])

OutreachRepoDep = Annotated[OutreachRepository, Depends(get_outreach_repo)]
EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
TraceRepoDep = Annotated[DebateTraceRepository, Depends(get_trace_repo)]
ObjectStorageDep = Annotated[ObjectStorage, Depends(get_object_storage)]


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


@router.get("/confirmations", response_model=GlobalResponse[list])
async def get_forwarding_confirmations(
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
) -> GlobalResponse:
    """Provider forwarding-confirmation emails (Gmail etc.) — never run through
    triage. The frontend surfaces these so the professor can grab the verify link."""
    confirmations = await outreach_repo.list_by_channel(
        current_professor.id, SYSTEM_CONFIRMATION_CHANNEL
    )
    return GlobalResponse(
        data=[o.model_dump(mode="json") for o in confirmations],
        message=f"{len(confirmations)} confirmation email(s)",
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


@router.post("/{outreach_id}/retriage", response_model=GlobalResponse[dict])
async def retriage_outreach(
    outreach_id: UUID,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    trace_repo: TraceRepoDep,
) -> GlobalResponse:
    """Reset an outreach to `pending_triage` and re-enqueue the Gatekeeper.

    Useful for stub/test rows created before triage was wired, or to re-run
    triage after the professor edits their custom instructions."""
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")

    # Drop the prior debate trace(s) so the replay never shows a stale run after
    # the re-triage produces a fresh one.
    await trace_repo.delete_by_outreach_id(outreach_id)

    outreach.status = OutreachStatus.PENDING_TRIAGE
    outreach.triage_verdict = None
    outreach.triage_reason = None
    outreach.decision = None
    outreach.extracted_profile = None
    outreach.extracted_claims = []
    outreach.debate_trace_id = None
    outreach.replied_at = None
    saved = await outreach_repo.save(outreach)

    triage_and_ingest.delay(str(saved.id), str(saved.professor_id))
    return GlobalResponse(data=saved.model_dump(mode="json"), message="Re-queued for triage")


@router.delete("/{outreach_id}", response_model=GlobalResponse[dict])
async def delete_outreach(
    outreach_id: UUID,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
) -> GlobalResponse:
    """Permanently remove an outreach (e.g. a stub/test row)."""
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")

    await outreach_repo.delete(outreach_id)
    return GlobalResponse(data={"id": str(outreach_id)}, message="Outreach deleted")


@router.get("/{outreach_id}/attachments/{index}")
async def download_attachment(
    outreach_id: UUID,
    index: int,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    object_storage: ObjectStorageDep,
) -> Response:
    """Stream a stored outreach attachment (e.g. a candidate CV) from object storage."""
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")
    if index < 0 or index >= len(outreach.attachment_keys):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    attachment = outreach.attachment_keys[index]
    try:
        data = await object_storage.download(attachment.storage_key)
    except NotFoundError as exc:
        # The reference exists on the outreach but the bytes were never uploaded
        # to R2 (e.g. legacy rows ingested before attachment upload was wired).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file is no longer available",
        ) from exc
    return Response(
        content=data,
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{attachment.filename}"'},
    )


@router.get("/{outreach_id}/debate", response_model=GlobalResponse[dict])
async def get_debate_trace(
    outreach_id: UUID,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    trace_repo: TraceRepoDep,
) -> GlobalResponse:
    """Return the full debate trace (turns, receipts, cross-references) for the
    replay surface. The trace is the centrepiece of the outreach-detail flow (§5.4):
    the professor reconstructs *why* a decision was made by replaying it."""
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")

    trace = await trace_repo.get_by_outreach_id(outreach_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No debate trace for this outreach yet",
        )
    return GlobalResponse(data=trace.model_dump(mode="json"), message="OK")


@router.get("/{outreach_id}/debate/turns/{index}/audio")
async def get_turn_audio(
    outreach_id: UUID,
    index: int,
    current_professor: CurrentProfessorDep,
    outreach_repo: OutreachRepoDep,
    trace_repo: TraceRepoDep,
    object_storage: ObjectStorageDep,
) -> Response:
    """Stream the synthesized speech for one debate turn, driving the replay's
    audio. 404 when a turn has no audio yet (synthesis pending or failed) — the
    replay treats that as a silent, heuristic-duration beat."""
    outreach = await outreach_repo.get_by_id(outreach_id)
    if not outreach or outreach.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach not found")

    trace = await trace_repo.get_by_outreach_id(outreach_id)
    if not trace or index < 0 or index >= len(trace.turns):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turn not found")

    audio_key = trace.turns[index].audio_key
    if not audio_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No audio for this turn"
        )
    try:
        data = await object_storage.download(audio_key)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turn audio is no longer available",
        ) from exc
    media_type = "audio/wav" if audio_key.endswith(".wav") else "audio/mpeg"
    return Response(content=data, media_type=media_type)


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
    # The professor is now actively deciding this one — pull it back into the
    # review queue even if it had auto-resolved (rejected), so the override is
    # actionable rather than stranded in a terminal tab.
    if outreach.status == OutreachStatus.REJECTED:
        outreach.status = OutreachStatus.AWAITING_REVIEW
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
