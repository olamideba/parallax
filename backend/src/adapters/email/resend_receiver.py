from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping

import httpx
from loguru import logger

from src.application.ports.outbound.email import InboundEmail, InboundEmailGateway
from src.config import get_settings
from src.domain.exceptions.base import IntakeError

_ATTACHMENT_URL = "https://api.resend.com/emails/attachments/{id}"


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
        data = payload.get("data", payload)
        to_field = data.get("to")
        recipient = to_field[0] if isinstance(to_field, list) else to_field
        return InboundEmail(
            recipient=recipient or "",
            sender_email=data.get("from", ""),
            sender_name=data.get("from_name"),
            subject=data.get("subject"),
            text_body=data.get("text") or "",
            html_body=data.get("html"),
            attachment_ids=[a["id"] for a in data.get("attachments", []) if "id" in a],
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
