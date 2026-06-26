from __future__ import annotations

import httpx
from loguru import logger

from src.application.ports.outbound.email import EmailSender
from src.config import get_settings
from src.domain.exceptions.base import IntakeError

_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailSender(EmailSender):
    async def send_reply(
        self,
        *,
        to_email: str,
        reply_to_email: str,
        subject: str,
        body_text: str,
    ) -> None:
        settings = get_settings()
        if not settings.BREVO_API_KEY:
            raise IntakeError("BREVO_API_KEY is not configured")

        payload = {
            "sender": {
                "name": settings.BREVO_SENDER_NAME,
                "email": settings.BREVO_SENDER_EMAIL,
            },
            "to": [{"email": to_email}],
            "replyTo": {"email": reply_to_email},
            "subject": subject,
            "textContent": body_text,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _BREVO_URL,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
        if resp.status_code >= 300:
            logger.error("Brevo send failed: {} {}", resp.status_code, resp.text)
            raise IntakeError(f"Brevo send failed with status {resp.status_code}")
