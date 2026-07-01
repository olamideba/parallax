from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from pydantic import BaseModel


class InboundEmail(BaseModel):
    """Provider-agnostic representation of a received email."""

    recipient: str  # the professor's intake address (the `to` field)
    sender_email: str  # the student's address (the `from` field)
    sender_name: str | None = None
    subject: str | None = None
    text_body: str = ""
    html_body: str | None = None
    attachment_ids: list[str] = []
    provider_message_id: str | None = None  # provider id used to fetch attachments
    is_system_confirmation: bool = False


class FetchedAttachment(BaseModel):
    """A downloaded inbound attachment ready to be persisted to object storage."""

    provider_id: str
    filename: str
    content_type: str | None = None
    data: bytes


class InboundEmailGateway(ABC):
    """Inbound email provider (currently Resend). Swap freely."""

    @abstractmethod
    def verify_signature(self, payload: bytes, headers: Mapping[str, str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, payload: dict) -> InboundEmail:
        """Build an InboundEmail from the webhook payload (metadata only — no body)."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_email(self, email_id: str) -> InboundEmail:
        """Fetch the full email (incl. text/html body) from the provider API."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_attachments(self, email_id: str) -> list[FetchedAttachment]:
        """Download all attachments for a received email (bytes + metadata)."""
        raise NotImplementedError


class EmailSender(ABC):
    """Outbound email provider (currently Brevo). Swap freely."""

    @abstractmethod
    async def send_reply(
        self,
        *,
        to_email: str,
        reply_to_email: str,
        subject: str,
        body_text: str,
    ) -> None:
        raise NotImplementedError
