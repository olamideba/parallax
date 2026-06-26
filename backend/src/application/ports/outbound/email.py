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


class InboundEmailGateway(ABC):
    """Inbound email provider (currently Resend). Swap freely."""

    @abstractmethod
    def verify_signature(self, payload: bytes, headers: Mapping[str, str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, payload: dict) -> InboundEmail:
        raise NotImplementedError

    @abstractmethod
    async def download_attachment(self, attachment_id: str) -> tuple[bytes, str]:
        """Return (file_bytes, filename) for a provider attachment id."""
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
