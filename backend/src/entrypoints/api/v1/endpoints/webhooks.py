from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from loguru import logger

from src.application.ports.outbound.email import InboundEmailGateway
from src.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
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
    inbound = gateway.parse(payload)
    outreach = await use_case.execute(inbound)
    if outreach is None:
        # Unknown intake address — discard but ack so Resend stops retrying.
        return Response(status_code=status.HTTP_200_OK)

    triage_and_ingest.delay(str(outreach.id), str(outreach.professor_id))
    logger.info("Inbound outreach {} queued for triage", outreach.id)
    return Response(status_code=status.HTTP_200_OK)
