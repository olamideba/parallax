from __future__ import annotations

from langchain_core.tools import tool

from src.adapters.qwen_cloud.tool_registry import tools_for_role
from src.domain.models.society import AgentRole


@tool
def fake_retrieval_tool(query: str) -> list[dict]:
    """Fake retrieval tool stand-in for tests."""
    return []


def _names(role: AgentRole) -> set[str]:
    return {t.name for t in tools_for_role(role, fake_retrieval_tool)}


def test_advocate_gets_retrieval_only() -> None:
    assert _names(AgentRole.ADVOCATE) == {"fake_retrieval_tool"}


def test_auditor_gets_retrieval_and_claim_verification() -> None:
    assert _names(AgentRole.AUDITOR) == {"fake_retrieval_tool", "claim_verification_tool"}


def test_assessor_gets_capacity_math_and_mobility_lookup() -> None:
    assert _names(AgentRole.ASSESSOR) == {"capacity_math_tool", "mobility_lookup_tool"}


def test_arbitrator_gets_no_tools() -> None:
    assert tools_for_role(AgentRole.ARBITRATOR, fake_retrieval_tool) == []


def test_gatekeeper_gets_no_debate_tools() -> None:
    # Gatekeeper doesn't participate in the debate toolset — it's a distinct,
    # earlier triage pass (see TriageOutreachUseCase / QwenGatekeeper).
    assert tools_for_role(AgentRole.GATEKEEPER, fake_retrieval_tool) == []
