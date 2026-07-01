from __future__ import annotations

from uuid import UUID

from loguru import logger

from src.application.ports.outbound.gatekeeper import Gatekeeper
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.publication_source import PdfTextExtractor
from src.application.ports.outbound.repository import (
    OutreachRepository,
    ProfessorRepository,
)
from src.domain.models.outreach import (
    Decision,
    DecisionLabel,
    ExtractedClaim,
    Outreach,
    OutreachStatus,
    TriageVerdict,
)

# Cap CV text fed to the cheap triage model — keeps token cost bounded.
_MAX_CV_CHARS = 12_000


class TriageOutreachUseCase:
    """Gatekeeper pass: extract a candidate profile + claims from the raw outreach
    (email body + attached CV text, *not* embedded) and decide promote vs. reject.

    Reject synthesises a `decline` decision and queues the outreach for the
    professor to see (and override) — never a silent drop, per the HITL rule.
    Promote leaves the outreach in `pending_triage` for the debate to pick up.
    """

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        professor_repo: ProfessorRepository,
        object_storage: ObjectStorage,
        pdf_extractor: PdfTextExtractor,
        gatekeeper: Gatekeeper,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._professor_repo = professor_repo
        self._object_storage = object_storage
        self._pdf_extractor = pdf_extractor
        self._gatekeeper = gatekeeper

    async def execute(self, outreach_id: UUID) -> TriageVerdict | None:
        outreach = await self._outreach_repo.get_by_id(outreach_id)
        if outreach is None:
            logger.warning("Triage: outreach {} not found", outreach_id)
            return None
        if outreach.status != OutreachStatus.PENDING_TRIAGE:
            # Already triaged (idempotent re-delivery) — don't redo work.
            return outreach.triage_verdict

        professor = await self._professor_repo.get_by_id(outreach.professor_id)
        if professor is None:
            logger.warning("Triage: professor {} not found", outreach.professor_id)
            return None

        cv_text = await self._extract_cv_text(outreach)
        assessment = await self._gatekeeper.assess(
            sender_email=outreach.sender_email,
            subject=outreach.subject,
            body=outreach.body,
            cv_text=cv_text,
            professor_topics=professor.capacity.recruiting_topics,
            custom_instructions=professor.custom_instructions,
            aggressiveness=professor.gatekeeper_aggressiveness,
        )

        outreach.extracted_profile = assessment.profile
        outreach.extracted_claims = [
            ExtractedClaim(text=text) for text in assessment.claim_texts
        ]
        outreach.triage_verdict = assessment.verdict

        if assessment.verdict == TriageVerdict.REJECT:
            # Land in the "Declined" tab, overridable by the professor.
            outreach.decision = Decision(
                label=DecisionLabel.DECLINE,
                rationale=f"Filtered at triage: {assessment.reason}",
            )
            outreach.status = OutreachStatus.AWAITING_REVIEW

        await self._outreach_repo.save(outreach)
        return assessment.verdict

    async def _extract_cv_text(self, outreach: Outreach) -> str | None:
        texts: list[str] = []
        for attachment in outreach.attachment_keys:
            is_pdf = attachment.filename.lower().endswith(".pdf") or (
                (attachment.content_type or "").endswith("pdf")
            )
            if not is_pdf:
                continue
            try:
                data = await self._object_storage.download(attachment.storage_key)
                texts.append(self._pdf_extractor.extract_text(data))
            except Exception as exc:  # noqa: BLE001 — a bad CV shouldn't block triage
                logger.warning(
                    "Triage: could not read attachment {}: {}",
                    attachment.storage_key,
                    exc,
                )
        if not texts:
            return None
        return "\n\n".join(texts)[:_MAX_CV_CHARS]
