from __future__ import annotations

from langchain_core.tools import BaseTool

from src.adapters.mcp.tools.mobility_lookup import mobility_lookup_tool
from src.adapters.qwen_cloud.tools.capacity_math import capacity_math_tool
from src.adapters.qwen_cloud.tools.claim_verification import claim_verification_tool
from src.domain.models.society import AgentRole


def tools_for_role(role: AgentRole, retrieval_tool: BaseTool) -> list[BaseTool]:
    """Which bindable tools a debate agent role gets.

    Tools are a shared toolkit, not role-locked implementations (§ item 3) —
    this function only decides which *subset* of the shared toolkit each role
    is handed via `bind_tools`. `retrieval_tool` is injected per-debate since
    it's scoped to one `professor_id`; the rest are stateless and shared.

    - Advocate: retrieval only — makes the case, cites the corpus.
    - Auditor: retrieval + claim-verification — cross-examines specific claims.
    - Assessor: capacity-math + mobility-lookup — feasibility, not research fit.
    - Arbitrator: none — resolves from the transcript only, introduces no new
      evidence of its own (see arbitrator.j2).
    """
    if role == AgentRole.ADVOCATE:
        return [retrieval_tool]
    if role == AgentRole.AUDITOR:
        return [retrieval_tool, claim_verification_tool]
    if role == AgentRole.ASSESSOR:
        return [capacity_math_tool, mobility_lookup_tool]
    return []
