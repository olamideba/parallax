from __future__ import annotations

from datetime import UTC, datetime

from loguru import logger
from uuid6 import uuid7

from src.application.ports.outbound.email import InboundEmail
from src.application.ports.outbound.repository import OutreachRepository, ProfessorRepository
from src.domain.models.outreach import Outreach, OutreachStatus


class ProcessInboundEmailUseCase:
    """Resolve an inbound email to its professor and persist an Outreach.

    Attachment download/storage is deferred (R2 stubbed); for now the provider
    attachment ids are recorded on the outreach as keys.
    """

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        professor_repo: ProfessorRepository,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._professor_repo = professor_repo

    async def execute(self, inbound: InboundEmail) -> Outreach | None:
        professor = await self._professor_repo.get_by_intake_email(inbound.recipient)
        if professor is None:
            logger.warning("Inbound email for unknown intake address: {}", inbound.recipient)
            return None

        outreach = Outreach(
            id=uuid7(),
            professor_id=professor.id,
            channel="email",
            sender_email=inbound.sender_email,
            sender_name=inbound.sender_name,
            subject=inbound.subject,
            body=inbound.text_body,
            body_html=inbound.html_body,
            attachment_keys=inbound.attachment_ids,
            received_at=datetime.now(UTC),
            status=OutreachStatus.PENDING_TRIAGE,
        )
        return await self._outreach_repo.save(outreach)
