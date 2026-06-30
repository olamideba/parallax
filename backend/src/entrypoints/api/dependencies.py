from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.auth.supabase_auth import get_professor_id_from_token
from src.adapters.email.brevo_sender import BrevoEmailSender
from src.adapters.email.resend_receiver import ResendInboundGateway
from src.adapters.ingestion.vector_index import PgVectorStore
from src.adapters.mcp.server import LocalMcpToolBus
from src.adapters.qwen_cloud.runtime import QwenLLMClient
from src.adapters.storage.database import get_session
from src.adapters.storage.models import ProfessorRecord
from src.adapters.storage.object_storage import R2ObjectStorage
from src.adapters.storage.repository_impl import (
    SqlDebateTraceRepository,
    SqlOutreachRepository,
    SqlProfessorRepository,
)
from src.application.ports.outbound.email import EmailSender, InboundEmailGateway
from src.application.ports.outbound.llm_client import LLMClient
from src.application.ports.outbound.mcp_tool_bus import McpToolBus
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
    ProfessorRepository,
)
from src.application.ports.outbound.vector_store import VectorStore
from src.application.use_cases.evaluate_candidate import EvaluateCandidateUseCase
from src.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from src.application.use_cases.process_ingestion import ProcessIngestionUseCase
from src.config import get_settings

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ProfessorIdDep = Annotated[UUID, Depends(get_professor_id_from_token)]


async def get_current_professor(
    professor_id: ProfessorIdDep,
    session: SessionDep,
) -> ProfessorRecord:
    record = await session.get(ProfessorRecord, professor_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor not found")
    return record


CurrentProfessorDep = Annotated[ProfessorRecord, Depends(get_current_professor)]


def get_llm_client() -> LLMClient:
    return QwenLLMClient()


def get_mcp_bus() -> McpToolBus:
    return LocalMcpToolBus()


def get_outreach_repo(session: SessionDep) -> OutreachRepository:
    return SqlOutreachRepository(session)


def get_professor_repo(session: SessionDep) -> ProfessorRepository:
    return SqlProfessorRepository(session)


def get_trace_repo(session: SessionDep) -> DebateTraceRepository:
    return SqlDebateTraceRepository(session)


def get_vector_store(session: SessionDep) -> VectorStore:
    return PgVectorStore(session)


def get_object_storage() -> ObjectStorage:
    return R2ObjectStorage()


def get_email_sender() -> EmailSender:
    return BrevoEmailSender()


def get_inbound_gateway() -> InboundEmailGateway:
    return ResendInboundGateway()


def get_process_inbound_email_use_case(
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
    professor_repo: Annotated[ProfessorRepository, Depends(get_professor_repo)],
) -> ProcessInboundEmailUseCase:
    return ProcessInboundEmailUseCase(outreach_repo, professor_repo)


def get_process_ingestion_use_case(
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ProcessIngestionUseCase:
    return ProcessIngestionUseCase(outreach_repo, llm_client, vector_store)


def get_evaluate_candidate_use_case(
    outreach_repo: Annotated[OutreachRepository, Depends(get_outreach_repo)],
    professor_repo: Annotated[ProfessorRepository, Depends(get_professor_repo)],
    trace_repo: Annotated[DebateTraceRepository, Depends(get_trace_repo)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    mcp_bus: Annotated[McpToolBus, Depends(get_mcp_bus)],
) -> EvaluateCandidateUseCase:
    settings = get_settings()
    return EvaluateCandidateUseCase(
        outreach_repo,
        professor_repo,
        trace_repo,
        llm_client,
        vector_store,
        mcp_bus,
        round_cap=settings.DEBATE_ROUND_CAP,
    )
