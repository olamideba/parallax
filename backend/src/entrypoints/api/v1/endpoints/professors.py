from __future__ import annotations

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid6 import uuid7

from src.adapters.email.intake import derive_intake_address
from src.adapters.storage.models import ProfessorRecord, PublicationRecord
from src.application.ports.outbound.email import InboundEmail
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from src.config import get_settings
from src.domain.models.professor import PublicationStatus
from src.entrypoints.api.dependencies import (
    CurrentProfessorDep,
    SessionDep,
    get_object_storage,
    get_process_inbound_email_use_case,
)
from src.entrypoints.api.schemas import GlobalResponse
from src.entrypoints.workers.ingestion_consumer import ingest_publication
from src.entrypoints.workers.intake_consumer import triage_and_ingest

router = APIRouter(prefix="/professors", tags=["professors"])

InboundUseCaseDep = Annotated[
    ProcessInboundEmailUseCase, Depends(get_process_inbound_email_use_case)
]


async def _ensure_intake_email(p: ProfessorRecord, session: AsyncSession) -> ProfessorRecord:
    if p.intake_email:
        return p
    settings = get_settings()
    if not (settings.HMAC_SECRET and settings.RESEND_INBOUND_DOMAIN):
        return p  # not configured — leave null
    p.intake_email = derive_intake_address(
        professor_id=str(p.id),
        professor_email=p.email,
        secret=settings.HMAC_SECRET,
        domain=settings.RESEND_INBOUND_DOMAIN,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


# --- Schemas ---

class UpdateProfessorRequest(BaseModel):
    display_name: str | None = None
    open_slots: int | None = None
    students_committed: int | None = None
    budget_amount: int | None = None
    funding_source: str | None = None
    recruiting_topics: list[str] | None = None
    gatekeeper_aggressiveness: float | None = None
    auto_resolve_declines: bool | None = None
    hold_when_at_capacity: bool | None = None


class PublicationInput(BaseModel):
    title: str | None = None
    doi: str | None = None
    url: str | None = None
    storage_key: str | None = None


# --- Helpers ---

def _professor_dict(p: ProfessorRecord) -> dict:
    return {
        "id": str(p.id),
        "email": p.email,
        "display_name": p.display_name,
        "intake_email": p.intake_email,
        "open_slots": p.open_slots,
        "students_committed": p.students_committed,
        "effective_open_slots": max(0, p.open_slots - p.students_committed),
        "budget_amount": p.budget_amount,
        "funding_source": p.funding_source,
        "recruiting_topics": json.loads(p.recruiting_topics),
        "gatekeeper_aggressiveness": p.gatekeeper_aggressiveness,
        "auto_resolve_declines": p.auto_resolve_declines,
        "hold_when_at_capacity": p.hold_when_at_capacity,
    }


def _publication_dict(p: PublicationRecord) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "doi": p.doi,
        "url": p.url,
        "indexed": p.indexed,
        "status": p.status,
        "storage_key": p.storage_key,
    }


# --- Endpoints ---

@router.get("/me", response_model=GlobalResponse[dict])
async def get_me(
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    p = await _ensure_intake_email(current_professor, session)
    return GlobalResponse(data=_professor_dict(p), message="OK")


@router.patch("/me", response_model=GlobalResponse[dict])
async def update_me(
    body: UpdateProfessorRequest,
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    p = current_professor
    if body.display_name is not None:
        p.display_name = body.display_name
    if body.open_slots is not None:
        p.open_slots = body.open_slots
    if body.students_committed is not None:
        p.students_committed = body.students_committed
    if body.budget_amount is not None:
        p.budget_amount = body.budget_amount
    if body.funding_source is not None:
        p.funding_source = body.funding_source
    if body.recruiting_topics is not None:
        p.recruiting_topics = json.dumps(body.recruiting_topics)
    if body.gatekeeper_aggressiveness is not None:
        p.gatekeeper_aggressiveness = body.gatekeeper_aggressiveness
    if body.auto_resolve_declines is not None:
        p.auto_resolve_declines = body.auto_resolve_declines
    if body.hold_when_at_capacity is not None:
        p.hold_when_at_capacity = body.hold_when_at_capacity

    session.add(p)
    await session.commit()
    await session.refresh(p)
    return GlobalResponse(data=_professor_dict(p), message="Profile updated")


@router.get("/me/publications", response_model=GlobalResponse[list])
async def get_my_publications(
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    result = await session.exec(
        select(PublicationRecord).where(
            PublicationRecord.professor_id == current_professor.id
        )
    )
    pubs = result.all()
    return GlobalResponse(
        data=[_publication_dict(p) for p in pubs],
        message=f"{len(pubs)} publication(s)",
    )


@router.put("/me/publications", response_model=GlobalResponse[list])
async def replace_my_publications(
    body: list[PublicationInput],
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    # Delete existing publications for this professor
    existing = await session.exec(
        select(PublicationRecord).where(
            PublicationRecord.professor_id == current_professor.id
        )
    )
    for pub in existing.all():
        await session.delete(pub)

    # Insert the new list
    new_pubs = [
        PublicationRecord(
            id=uuid7(),
            professor_id=current_professor.id,
            title=p.title,
            doi=p.doi,
            url=p.url,
            storage_key=p.storage_key,
            indexed=False,
            status=PublicationStatus.PENDING.value,
        )
        for p in body
    ]
    for pub in new_pubs:
        session.add(pub)

    await session.commit()

    # Dispatch ingestion for each publication with a resolvable source.
    for pub in new_pubs:
        if pub.storage_key or pub.url or pub.doi:
            ingest_publication.delay(str(pub.id))

    return GlobalResponse(
        data=[_publication_dict(p) for p in new_pubs],
        message=f"{len(new_pubs)} publication(s) saved",
    )


@router.post("/me/publications", response_model=GlobalResponse[dict])
async def add_publication(
    body: PublicationInput,
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    """Append a single publication without touching existing ones."""
    pub = PublicationRecord(
        id=uuid7(),
        professor_id=current_professor.id,
        title=body.title,
        doi=body.doi,
        url=body.url,
        storage_key=body.storage_key,
        indexed=False,
        status=PublicationStatus.PENDING.value,
    )
    session.add(pub)
    await session.commit()
    await session.refresh(pub)

    if pub.storage_key or pub.url or pub.doi:
        ingest_publication.delay(str(pub.id))

    return GlobalResponse(data=_publication_dict(pub), message="Publication added")


@router.post("/me/publications/{publication_id}/ingest", response_model=GlobalResponse[dict])
async def reingest_publication(
    publication_id: UUID,
    current_professor: CurrentProfessorDep,
    session: SessionDep,
) -> GlobalResponse:
    """(Re)trigger ingestion for one publication — e.g. after a manual PDF upload."""
    pub = await session.get(PublicationRecord, publication_id)
    if pub is None or pub.professor_id != current_professor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
    if not (pub.storage_key or pub.url or pub.doi):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Publication has no storage_key, url, or doi to ingest",
        )
    ingest_publication.delay(str(pub.id))
    return GlobalResponse(
        data=_publication_dict(pub),
        message="Ingestion queued",
    )


ObjectStorageDep = Annotated[ObjectStorage, Depends(get_object_storage)]


@router.post("/me/publications/upload", response_model=GlobalResponse[dict])
async def upload_publication_pdf(
    current_professor: CurrentProfessorDep,
    session: SessionDep,
    storage: ObjectStorageDep,
    file: Annotated[UploadFile, File()],
    publication_id: Annotated[UUID | None, Form()] = None,
) -> GlobalResponse:
    """Upload a PDF to object storage and return its storage_key.

    If `publication_id` is supplied, the key is attached to that publication and
    ingestion is (re)dispatched — the path for retrying a `needs_upload`/`failed`
    item. Otherwise the caller includes the returned `storage_key` in a
    subsequent PUT /me/publications.
    """
    settings = get_settings()
    data = await file.read()

    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the {settings.UPLOAD_MAX_MB} MB limit",
        )
    if not (file.content_type == "application/pdf" or data.startswith(b"%PDF")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF uploads are supported",
        )

    storage_key = f"publications/{current_professor.id}/{uuid7()}.pdf"
    await storage.upload(storage_key, data, "application/pdf")

    publication: dict | None = None
    if publication_id is not None:
        pub = await session.get(PublicationRecord, publication_id)
        if pub is None or pub.professor_id != current_professor.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found"
            )
        pub.storage_key = storage_key
        pub.status = PublicationStatus.PENDING.value
        pub.indexed = False
        session.add(pub)
        await session.commit()
        await session.refresh(pub)
        ingest_publication.delay(str(pub.id))
        publication = _publication_dict(pub)

    return GlobalResponse(
        data={"storage_key": storage_key, "publication": publication},
        message="Upload stored",
    )


@router.post("/me/intake/test", response_model=GlobalResponse[dict])
async def send_test_intake(
    current_professor: CurrentProfessorDep,
    session: SessionDep,
    use_case: InboundUseCaseDep,
) -> GlobalResponse:
    """Fire a synthetic inbound email so the professor can verify the pipeline
    end-to-end before setting up real forwarding."""
    p = await _ensure_intake_email(current_professor, session)
    if not p.intake_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Intake address not configured (HMAC_SECRET / RESEND_INBOUND_DOMAIN unset)",
        )

    synthetic = InboundEmail(
        recipient=p.intake_email,
        sender_email="prospective.student@example.edu",
        sender_name="Test Student",
        subject="Test outreach — verifying Parallax intake",
        text_body=(
            "Hello Professor,\n\nThis is a synthetic test email generated by "
            "Parallax to confirm your intake pipeline is working.\n\nBest,\nTest Student"
        ),
    )
    outreach = await use_case.execute(synthetic)
    if outreach is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve intake address to this professor",
        )

    triage_and_ingest.delay(str(outreach.id), str(outreach.professor_id))
    return GlobalResponse(
        data={"outreach_id": str(outreach.id), "intake_email": p.intake_email},
        message="Test email injected into the intake pipeline",
    )
