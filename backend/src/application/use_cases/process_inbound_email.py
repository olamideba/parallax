from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from loguru import logger
from uuid6 import uuid7

from src.application.ports.outbound.email import InboundEmail, InboundEmailGateway
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.repository import OutreachRepository, ProfessorRepository
from src.domain.models.outreach import (
    EMAIL_CHANNEL,
    SYSTEM_CONFIRMATION_CHANNEL,
    Attachment,
    Outreach,
    OutreachStatus,
)

# Window for content-based duplicate detection. Guards against upstream
# duplicate delivery (e.g. the sending MTA retrying SMTP before Resend's
# receiving MX acks fast enough) that shows up as distinct provider events —
# each with its own provider_message_id — for what is actually one email.
_DUPLICATE_WINDOW = timedelta(minutes=10)


class ProcessInboundEmailUseCase:
    """Resolve an inbound email to its professor and persist an Outreach.

    Provider attachments are downloaded and copied into object storage (R2) so
    the outreach references stable storage keys + original filenames, not opaque
    provider ids that expire. A failed attachment download is logged and skipped
    rather than dropping the whole email.
    """

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        professor_repo: ProfessorRepository,
        inbound_gateway: InboundEmailGateway,
        object_storage: ObjectStorage,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._professor_repo = professor_repo
        self._inbound_gateway = inbound_gateway
        self._object_storage = object_storage

    async def execute(self, inbound: InboundEmail) -> Outreach | None:
        professor = await self._professor_repo.get_by_intake_email(inbound.recipient)
        if professor is None:
            logger.warning("Inbound email for unknown intake address: {}", inbound.recipient)
            return None

        # Idempotency #1: the same provider event redelivered (webhook retry).
        if inbound.provider_message_id:
            existing = await self._outreach_repo.get_by_provider_message_id(
                inbound.provider_message_id
            )
            if existing is not None:
                logger.info(
                    "Duplicate webhook for email {} — reusing outreach {}",
                    inbound.provider_message_id,
                    existing.id,
                )
                return existing

        # Idempotency #2: a genuinely distinct provider event for what is the
        # same underlying email (e.g. upstream MTA retry before the provider's
        # receiving MX). No shared provider id to key off, so match on identical
        # sender/subject/body from the same professor within a short window.
        duplicate = await self._outreach_repo.find_recent_duplicate(
            professor_id=professor.id,
            sender_email=inbound.sender_email,
            subject=inbound.subject,
            body=inbound.text_body,
            since=datetime.now(UTC) - _DUPLICATE_WINDOW,
        )
        if duplicate is not None:
            logger.info(
                "Duplicate inbound email from {} — reusing outreach {}",
                inbound.sender_email,
                duplicate.id,
            )
            return duplicate

        channel = (
            SYSTEM_CONFIRMATION_CHANNEL
            if inbound.is_system_confirmation
            else EMAIL_CHANNEL
        )
        outreach_id = uuid7()
        attachments = await self._store_attachments(outreach_id, inbound)
        outreach = Outreach(
            id=outreach_id,
            professor_id=professor.id,
            channel=channel,
            sender_email=inbound.sender_email,
            sender_name=inbound.sender_name,
            subject=inbound.subject,
            body=inbound.text_body,
            body_html=inbound.html_body,
            attachment_keys=attachments,
            provider_message_id=inbound.provider_message_id,
            received_at=datetime.now(UTC),
            status=OutreachStatus.PENDING_TRIAGE,
        )
        return await self._outreach_repo.save(outreach)

    async def _store_attachments(
        self, outreach_id: UUID, inbound: InboundEmail
    ) -> list[Attachment]:
        if not inbound.attachment_ids or not inbound.provider_message_id:
            return []

        try:
            fetched = await self._inbound_gateway.fetch_attachments(inbound.provider_message_id)
        except Exception as exc:  # noqa: BLE001 — never drop the email over attachments
            logger.warning(
                "Could not fetch attachments for email {}: {}", inbound.provider_message_id, exc
            )
            return []

        stored: list[Attachment] = []
        for att in fetched:
            try:
                storage_key = f"outreach/{outreach_id}/{att.provider_id}/{att.filename}"
                await self._object_storage.upload(
                    storage_key, att.data, att.content_type or "application/octet-stream"
                )
                stored.append(
                    Attachment(
                        storage_key=storage_key,
                        filename=att.filename,
                        content_type=att.content_type,
                    )
                )
                logger.info("Stored attachment {} -> {}", att.provider_id, storage_key)
            except Exception as exc:  # noqa: BLE001 — never drop the email over one bad file
                logger.warning("Could not store attachment {}: {}", att.provider_id, exc)
        return stored
