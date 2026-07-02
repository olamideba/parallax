from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.adapters.qwen_cloud.chat_model import get_chat_model
from src.adapters.qwen_cloud.skills.loader import load_skill_instructions
from src.domain.models.society import AgentRole


class ClaimVerdict(BaseModel):
    verdict: str = Field(description='One of: "verified", "refuted", "unclear".')
    receipt: str | None = Field(
        default=None, description="The exact retrieved chunk text relied on, if any."
    )
    reasoning: str = Field(description="One or two sentences explaining the verdict.")


async def verify_claim(claim: str, evidence_chunks: list[str]) -> ClaimVerdict:
    """Judge a candidate's claim against retrieved evidence (SKILL: claim-verification)."""
    instructions = load_skill_instructions("claim-verification")
    evidence_block = (
        "\n---\n".join(evidence_chunks) if evidence_chunks else "(no evidence retrieved)"
    )
    prompt = f"{instructions}\n\nCLAIM:\n{claim}\n\nRETRIEVED EVIDENCE CHUNKS:\n{evidence_block}"

    model = get_chat_model(AgentRole.AUDITOR).with_structured_output(ClaimVerdict)
    result = await model.ainvoke(prompt)
    return result if isinstance(result, ClaimVerdict) else ClaimVerdict(**dict(result))


@tool
async def claim_verification_tool(claim: str, evidence_chunks: list[str]) -> dict:
    """Judge whether a candidate's claim is verified, refuted, or unclear against
    retrieved evidence chunks from the professor's corpus. Use this whenever
    assessing a specific, checkable factual claim the candidate made about
    themselves — never assert a claim's truth without calling this."""
    result = await verify_claim(claim, evidence_chunks)
    return result.model_dump()
