from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from loguru import logger

from src.application.ports.outbound.email import InboundEmailGateway
from src.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from src.domain.models.outreach import SYSTEM_CONFIRMATION_CHANNEL
from src.entrypoints.api.dependencies import (
    get_inbound_gateway,
    get_process_inbound_email_use_case,
)
from src.entrypoints.workers.intake_consumer import triage_and_ingest

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

GatewayDep = Annotated[InboundEmailGateway, Depends(get_inbound_gateway)]
InboundUseCaseDep = Annotated[
    ProcessInboundEmailUseCase, Depends(get_process_inbound_email_use_case)
]


@router.post("/email/inbound")
async def email_inbound(
    request: Request,
    gateway: GatewayDep,
    use_case: InboundUseCaseDep,
) -> Response:
    """Resend inbound webhook (email.received). Always returns 2xx so Resend
    does not retry on application-level discards (unknown recipient, etc.)."""
    raw = await request.body()
    if not gateway.verify_signature(raw, request.headers):
        # Bad signature — reject so a forged caller gets a clear error.
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = json.loads(raw)
    # Webhook is metadata-only; fetch the full body from the Resend API.
    inbound = gateway.parse(payload)
    email_id = payload.get("data", {}).get("email_id")
    if email_id:
        try:
            inbound = await gateway.fetch_email(email_id)
        except Exception as exc:  # noqa: BLE001 — fall back to metadata, still ack
            logger.warning("Could not fetch full email {}: {}", email_id, exc)

    outreach = await use_case.execute(inbound)
    if outreach is None:
        # Unknown intake address — discard but ack so Resend stops retrying.
        return Response(status_code=status.HTTP_200_OK)

    if outreach.channel == SYSTEM_CONFIRMATION_CHANNEL:
        # Provider forwarding-confirmation email — store for the UI, don't triage.
        logger.info("Forwarding-confirmation email {} stored (no triage)", outreach.id)
        return Response(status_code=status.HTTP_200_OK)

    triage_and_ingest.delay(str(outreach.id), str(outreach.professor_id))
    logger.info("Inbound outreach {} queued for triage", outreach.id)
    return Response(status_code=status.HTTP_200_OK)
