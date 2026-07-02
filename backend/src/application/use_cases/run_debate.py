from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from loguru import logger

from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
    ProfessorRepository,
)
from src.domain.collaboration.negotiation_engine import NegotiationEngine
from src.domain.models.outreach import OutreachStatus, TriageVerdict
from src.domain.models.professor import Professor

# The engine is scoped to a professor (its retriever is per-corpus), so it can't
# be built until the professor is loaded. The composition root supplies a
# factory that wires the adapters; the use case stays ports + domain only.
EngineFactory = Callable[[Professor], NegotiationEngine]


class RunDebateUseCase:
    """Run the debate society for a promoted outreach, persist the trace, and
    attach the Arbitrator's decision — leaving the outreach in `awaiting_review`
    for the professor. Never sends anything; approval is a separate step."""

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        professor_repo: ProfessorRepository,
        trace_repo: DebateTraceRepository,
        engine_factory: EngineFactory,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._professor_repo = professor_repo
        self._trace_repo = trace_repo
        self._engine_factory = engine_factory

    async def execute(self, outreach_id: UUID) -> UUID | None:
        outreach = await self._outreach_repo.get_by_id(outreach_id)
        if outreach is None:
            logger.warning("Debate: outreach {} not found", outreach_id)
            return None
        if outreach.status != OutreachStatus.PENDING_TRIAGE:
            # Already debated (idempotent re-delivery) — don't redo the work.
            return outreach.debate_trace_id
        if outreach.triage_verdict != TriageVerdict.PROMOTE:
            logger.warning("Debate: outreach {} was not promoted, skipping", outreach_id)
            return None

        professor = await self._professor_repo.get_by_id(outreach.professor_id)
        if professor is None:
            logger.warning("Debate: professor {} not found", outreach.professor_id)
            return None

        engine = self._engine_factory(professor)
        outcome = await engine.run(outreach, professor)

        saved_trace = await self._trace_repo.save(outcome.trace)
        outreach.debate_trace_id = saved_trace.id
        outreach.decision = outcome.decision
        outreach.status = OutreachStatus.AWAITING_REVIEW
        await self._outreach_repo.save(outreach)
        logger.info(
            "Debate complete for outreach {}: {} ({} turns)",
            outreach_id,
            outcome.decision.label.value,
            len(outcome.trace.turns),
        )
        return saved_trace.id
