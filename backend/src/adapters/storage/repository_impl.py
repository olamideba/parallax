from __future__ import annotations

import json
from uuid import UUID

from sqlmodel import col, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.storage.models import (
    DebateTraceRecord,
    OutreachRecord,
    ProfessorRecord,
    PublicationChunkRecord,
    PublicationRecord,
)
from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
    ProfessorRepository,
    PublicationRepository,
)
from src.domain.models.outreach import (
    SYSTEM_CONFIRMATION_CHANNEL,
    Attachment,
    Decision,
    DecisionLabel,
    ExtractedClaim,
    ExtractedProfile,
    Outreach,
    OutreachStatus,
    TriageVerdict,
)
from src.domain.models.professor import (
    Capacity,
    Professor,
    Publication,
    PublicationStatus,
)
from src.domain.models.society import DebateTrace, DebateTurn

# --- Outreach mapping ---

def _deserialize_attachments(raw: str) -> list[Attachment]:
    """Parse the JSON attachment column, tolerating legacy plain-string keys
    (rows written before attachments carried filenames / R2 keys)."""
    items = json.loads(raw)
    attachments: list[Attachment] = []
    for item in items:
        if isinstance(item, str):
            attachments.append(Attachment(storage_key=item, filename=item))
        else:
            attachments.append(Attachment.model_validate(item))
    return attachments


def _record_to_outreach(r: OutreachRecord) -> Outreach:
    decision = None
    if r.decision_label:
        decision = Decision(
            label=DecisionLabel(r.decision_label),
            rationale=r.decision_rationale or "",
            drafted_reply=r.drafted_reply,
            overridden_by_professor=r.overridden_by_professor,
        )
    return Outreach(
        id=r.id,
        professor_id=r.professor_id,
        channel=r.channel,
        sender_email=r.sender_email,
        sender_name=r.sender_name,
        subject=r.subject,
        body=r.body,
        body_html=r.body_html,
        attachment_keys=_deserialize_attachments(r.attachment_keys),
        received_at=r.received_at,
        status=OutreachStatus(r.status),
        replied_at=r.replied_at,
        triage_verdict=TriageVerdict(r.triage_verdict) if r.triage_verdict else None,
        debate_trace_id=r.debate_trace_id,
        extracted_profile=(
            ExtractedProfile.model_validate_json(r.extracted_profile_json)
            if r.extracted_profile_json
            else None
        ),
        extracted_claims=(
            [ExtractedClaim.model_validate(c) for c in json.loads(r.extracted_claims_json)]
            if r.extracted_claims_json
            else []
        ),
        decision=decision,
    )


def _outreach_to_record(o: Outreach) -> OutreachRecord:
    return OutreachRecord(
        id=o.id,
        professor_id=o.professor_id,
        channel=o.channel,
        sender_email=o.sender_email,
        sender_name=o.sender_name,
        subject=o.subject,
        body=o.body,
        body_html=o.body_html,
        attachment_keys=json.dumps([a.model_dump() for a in o.attachment_keys]),
        received_at=o.received_at,
        status=o.status.value,
        replied_at=o.replied_at,
        triage_verdict=o.triage_verdict,
        debate_trace_id=o.debate_trace_id,
        decision_label=o.decision.label if o.decision else None,
        decision_rationale=o.decision.rationale if o.decision else None,
        drafted_reply=o.decision.drafted_reply if o.decision else None,
        overridden_by_professor=o.decision.overridden_by_professor if o.decision else False,
        extracted_profile_json=(
            o.extracted_profile.model_dump_json() if o.extracted_profile else None
        ),
        extracted_claims_json=(
            json.dumps([c.model_dump() for c in o.extracted_claims]) if o.extracted_claims else None
        ),
    )


# --- Professor mapping ---

def _record_to_professor(r: ProfessorRecord, pubs: list[PublicationRecord]) -> Professor:
    return Professor(
        id=r.id,
        email=r.email,
        display_name=r.display_name,
        intake_email=r.intake_email,
        capacity=Capacity(
            open_slots=r.open_slots,
            students_committed=r.students_committed,
            budget_amount=r.budget_amount,
            funding_source=r.funding_source,
            recruiting_topics=json.loads(r.recruiting_topics),
            auto_resolve_declines=r.auto_resolve_declines,
            hold_when_at_capacity=r.hold_when_at_capacity,
        ),
        gatekeeper_aggressiveness=r.gatekeeper_aggressiveness,
        publications=[_record_to_publication(p) for p in pubs],
    )


def _record_to_publication(p: PublicationRecord) -> Publication:
    return Publication(
        id=p.id,
        professor_id=p.professor_id,
        title=p.title,
        doi=p.doi,
        url=p.url,
        storage_key=p.storage_key,
        indexed=p.indexed,
        status=PublicationStatus(p.status),
    )


# --- DebateTrace mapping ---

def _record_to_trace(r: DebateTraceRecord) -> DebateTrace:
    return DebateTrace(
        id=r.id,
        outreach_id=r.outreach_id,
        professor_id=r.professor_id,
        turns=[DebateTurn.model_validate(t) for t in json.loads(r.turns_json)],
        round_cap=r.round_cap,
        terminated_at_round=r.terminated_at_round,
        started_at=r.started_at,
        ended_at=r.ended_at,
    )


def _trace_to_record(t: DebateTrace) -> DebateTraceRecord:
    return DebateTraceRecord(
        id=t.id,
        outreach_id=t.outreach_id,
        professor_id=t.professor_id,
        round_cap=t.round_cap,
        terminated_at_round=t.terminated_at_round,
        started_at=t.started_at,
        ended_at=t.ended_at,
        turns_json=json.dumps([turn.model_dump(mode="json") for turn in t.turns]),
    )


# --- Repository implementations ---

class SqlOutreachRepository(OutreachRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, outreach: Outreach) -> Outreach:
        record = _outreach_to_record(outreach)
        merged = await self._session.merge(record)
        await self._session.commit()
        await self._session.refresh(merged)
        return _record_to_outreach(merged)

    async def get_by_id(self, outreach_id: UUID) -> Outreach | None:
        record = await self._session.get(OutreachRecord, outreach_id)
        return _record_to_outreach(record) if record else None

    async def list_by_verdict(
        self, professor_id: UUID, verdict: TriageVerdict | None = None
    ) -> list[Outreach]:
        stmt = (
            select(OutreachRecord)
            .where(OutreachRecord.professor_id == professor_id)
            .where(OutreachRecord.channel != SYSTEM_CONFIRMATION_CHANNEL)
            .order_by(OutreachRecord.received_at.desc())
        )
        if verdict is not None:
            stmt = stmt.where(OutreachRecord.triage_verdict == verdict.value)
        result = await self._session.exec(stmt)
        return [_record_to_outreach(r) for r in result.all()]

    async def list_by_channel(self, professor_id: UUID, channel: str) -> list[Outreach]:
        stmt = (
            select(OutreachRecord)
            .where(OutreachRecord.professor_id == professor_id)
            .where(OutreachRecord.channel == channel)
            .order_by(OutreachRecord.received_at.desc())
        )
        result = await self._session.exec(stmt)
        return [_record_to_outreach(r) for r in result.all()]


class SqlProfessorRepository(ProfessorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, professor: Professor) -> Professor:
        record = ProfessorRecord(
            id=professor.id,
            email=professor.email,
            display_name=professor.display_name,
            intake_email=professor.intake_email,
            open_slots=professor.capacity.open_slots,
            students_committed=professor.capacity.students_committed,
            budget_amount=professor.capacity.budget_amount,
            funding_source=professor.capacity.funding_source,
            recruiting_topics=json.dumps(professor.capacity.recruiting_topics),
            gatekeeper_aggressiveness=professor.gatekeeper_aggressiveness,
            auto_resolve_declines=professor.capacity.auto_resolve_declines,
            hold_when_at_capacity=professor.capacity.hold_when_at_capacity,
        )
        merged = await self._session.merge(record)
        await self._session.commit()
        await self._session.refresh(merged)
        pubs = await self._get_publications(merged.id)
        return _record_to_professor(merged, pubs)

    async def get_by_id(self, professor_id: UUID) -> Professor | None:
        record = await self._session.get(ProfessorRecord, professor_id)
        if not record:
            return None
        pubs = await self._get_publications(professor_id)
        return _record_to_professor(record, pubs)

    async def get_by_email(self, email: str) -> Professor | None:
        result = await self._session.exec(
            select(ProfessorRecord).where(ProfessorRecord.email == email)
        )
        record = result.first()
        if not record:
            return None
        pubs = await self._get_publications(record.id)
        return _record_to_professor(record, pubs)

    async def get_by_intake_email(self, intake_email: str) -> Professor | None:
        result = await self._session.exec(
            select(ProfessorRecord).where(ProfessorRecord.intake_email == intake_email)
        )
        record = result.first()
        if not record:
            return None
        pubs = await self._get_publications(record.id)
        return _record_to_professor(record, pubs)

    async def _get_publications(self, professor_id: UUID) -> list[PublicationRecord]:
        result = await self._session.exec(
            select(PublicationRecord).where(PublicationRecord.professor_id == professor_id)
        )
        return list(result.all())


class SqlDebateTraceRepository(DebateTraceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, trace: DebateTrace) -> DebateTrace:
        record = _trace_to_record(trace)
        merged = await self._session.merge(record)
        await self._session.commit()
        await self._session.refresh(merged)
        return _record_to_trace(merged)

    async def get_by_outreach_id(self, outreach_id: UUID) -> DebateTrace | None:
        result = await self._session.exec(
            select(DebateTraceRecord).where(DebateTraceRecord.outreach_id == outreach_id)
        )
        record = result.first()
        return _record_to_trace(record) if record else None


class SqlPublicationRepository(PublicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, publication_id: UUID) -> Publication | None:
        record = await self._session.get(PublicationRecord, publication_id)
        return _record_to_publication(record) if record else None

    async def save(self, publication: Publication) -> Publication:
        record = PublicationRecord(
            id=publication.id,
            professor_id=publication.professor_id,
            title=publication.title,
            doi=publication.doi,
            url=publication.url,
            storage_key=publication.storage_key,
            indexed=publication.indexed,
            status=publication.status.value,
        )
        merged = await self._session.merge(record)
        await self._session.commit()
        await self._session.refresh(merged)
        return _record_to_publication(merged)

    async def clear_chunks(self, publication_id: UUID) -> None:
        await self._session.exec(
            delete(PublicationChunkRecord).where(
                col(PublicationChunkRecord.publication_id) == publication_id
            )
        )
        await self._session.commit()
