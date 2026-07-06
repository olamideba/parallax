from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    GATEKEEPER = "gatekeeper"
    ADVOCATE = "advocate"
    AUDITOR = "auditor"
    ASSESSOR = "assessor"
    ARBITRATOR = "arbitrator"


class ActionKind(StrEnum):
    """How an agent reached for grounding during a turn.

    - SKILL:     a custom, encapsulated capability (e.g. claim-verification)
    - MCP:       a call out to an MCP server / tool (e.g. web-search, scholarly-index)
    - RETRIEVAL: RAG over the professor's own indexed corpus (pgvector)
    """

    SKILL = "skill"
    MCP = "mcp"
    RETRIEVAL = "retrieval"


class AgentAction(BaseModel):
    """A tool/skill/retrieval the agent invoked while producing a turn.

    Recorded so the replay can *show* the engineering depth (custom Skills + MCP
    integrations) rather than leaving it invisible inside the LLM call.
    """

    kind: ActionKind
    name: str
    detail: str | None = None
    source: str | None = None  # MCP server id / skill id / index name


class Receipt(BaseModel):
    source_title: str
    chunk_text: str
    relevance_note: str | None = None


class DebateTurn(BaseModel):
    round: int
    role: AgentRole
    content: str
    receipts: list[Receipt] = Field(default_factory=list)
    actions: list[AgentAction] = Field(default_factory=list)
    references_turn_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    # Filled in after the debate by the audio-synthesis step, never by the
    # debate itself. `content` stays the full evidentiary record; `spoken_line`
    # is a short conversational rendering used only for TTS. `audio_duration_ms`
    # is the real playback length that drives the replay clock (the frontend
    # falls back to a character-count heuristic when it is absent).
    spoken_line: str | None = None
    audio_key: str | None = None
    audio_duration_ms: int | None = None


class DebateTrace(BaseModel):
    id: UUID
    outreach_id: UUID
    professor_id: UUID
    turns: list[DebateTurn] = Field(default_factory=list)
    round_cap: int
    terminated_at_round: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
