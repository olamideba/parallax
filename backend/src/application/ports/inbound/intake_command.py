from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IntakeCommand(BaseModel):
    channel: str = "email"
    sender_email: str
    sender_name: str | None = None
    body: str
    attachment_keys: list[str] = []
    received_at: datetime
