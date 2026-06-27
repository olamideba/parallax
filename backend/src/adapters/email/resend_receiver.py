from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping
from email.utils import parseaddr

import httpx
from loguru import logger

from src.adapters.email.confirmation import is_forwarding_confirmation
from src.application.ports.outbound.email import InboundEmail, InboundEmailGateway
from src.config import get_settings
from src.domain.exceptions.base import IntakeError

_ATTACHMENT_URL = "https://api.resend.com/emails/attachments/{id}"
_RECEIVED_URL = "https://api.resend.com/emails/receiving/{id}"


class ResendInboundGateway(InboundEmailGateway):
    def verify_signature(self, payload: bytes, headers: Mapping[str, str]) -> bool:
        """Verify a Resend (Svix) webhook signature.

        Resend signs webhooks with the Svix scheme: the signed content is
        `{svix-id}.{svix-timestamp}.{body}` HMAC-SHA256'd with the base64
        secret (the part after the `whsec_` prefix), base64-encoded.
        """
        secret = get_settings().RESEND_WEBHOOK_SECRET
        if not secret:
            # No secret configured (local/dev) — accept without verifying.
            logger.warning("RESEND_WEBHOOK_SECRET unset — skipping signature check")
            return True

        svix_id = headers.get("svix-id") or headers.get("webhook-id")
        svix_timestamp = headers.get("svix-timestamp") or headers.get("webhook-timestamp")
        svix_signature = headers.get("svix-signature") or headers.get("webhook-signature")
        if not (svix_id and svix_timestamp and svix_signature):
            return False

        signed_content = f"{svix_id}.{svix_timestamp}.{payload.decode()}".encode()
        key = secret.split("_", 1)[1] if secret.startswith("whsec_") else secret
        secret_bytes = base64.b64decode(key)
        expected = base64.b64encode(
            hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()
        ).decode()

        for part in svix_signature.split():
            _, _, sig = part.partition(",")
            if sig and hmac.compare_digest(sig, expected):
                return True
        return False

    def parse(self, payload: dict) -> InboundEmail:
        # Webhook payload is metadata only — text/html will be empty here.
        return self._to_inbound(payload.get("data", payload))

    async def fetch_email(self, email_id: str) -> InboundEmail:
        settings = get_settings()
        if not settings.RESEND_API_KEY:
            raise IntakeError("RESEND_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                _RECEIVED_URL.format(id=email_id),
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
        return self._to_inbound(data)

    @staticmethod
    def _to_inbound(data: dict) -> InboundEmail:
        # The intake address is in `to`; fall back to `received_for`.
        to_field = data.get("to") or data.get("received_for") or []
        recipient = to_field if isinstance(to_field, str) else (to_field[0] if to_field else "")
        # `from` is an RFC 5322 header: "Alice Chen <alice@mit.edu>" or just the address.
        display_name, address = parseaddr(data.get("from", ""))
        sender_email = address or data.get("from", "")
        subject = data.get("subject")
        return InboundEmail(
            recipient=recipient,
            sender_email=sender_email,
            sender_name=display_name or None,
            subject=subject,
            text_body=data.get("text") or "",
            html_body=data.get("html"),
            attachment_ids=[a["id"] for a in data.get("attachments", []) if "id" in a],
            is_system_confirmation=is_forwarding_confirmation(sender_email, subject),
        )

    async def download_attachment(self, attachment_id: str) -> tuple[bytes, str]:
        settings = get_settings()
        if not settings.RESEND_API_KEY:
            raise IntakeError("RESEND_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=60.0) as client:
            meta = await client.get(
                _ATTACHMENT_URL.format(id=attachment_id),
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            )
            meta.raise_for_status()
            info = meta.json()
            download_url = info["download_url"]
            filename = info.get("filename", attachment_id)
            file_resp = await client.get(download_url)
            file_resp.raise_for_status()
        return file_resp.content, filename
