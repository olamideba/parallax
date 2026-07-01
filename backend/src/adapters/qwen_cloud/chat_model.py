from __future__ import annotations

from langchain_qwq import ChatQwen
from pydantic import SecretStr

from src.adapters.qwen_cloud.compliance import assert_qwen_host
from src.config import get_settings
from src.domain.models.society import AgentRole


# Which configured Qwen model each agent role runs on. Debaters share the
# mid-tier model; the Gatekeeper is the cheap triage pass; the Arbitrator
# gets the stronger model for the final resolution.
def _model_for_role(role: AgentRole | None) -> str:
    settings = get_settings()
    mapping = {
        AgentRole.GATEKEEPER: settings.QWEN_MODEL_GATEKEEPER,
        AgentRole.ADVOCATE: settings.QWEN_MODEL_DEBATE,
        AgentRole.AUDITOR: settings.QWEN_MODEL_DEBATE,
        AgentRole.ASSESSOR: settings.QWEN_MODEL_DEBATE,
        AgentRole.ARBITRATOR: settings.QWEN_MODEL_ARBITRATOR,
    }
    if role is None:
        return settings.QWEN_MODEL_DEBATE
    return mapping[role]


def get_chat_model(role: AgentRole | None = None) -> ChatQwen:
    """Build the LangChain chat model for a debate agent.

    Single chokepoint for constructing a Qwen chat client: reads endpoint +
    key from config only, pins the per-role model, and refuses to point at any
    non-Qwen host (hackathon compliance). The debate agents (LangGraph nodes)
    use this; embeddings/RAG stay on `QwenLLMClient`.
    """
    settings = get_settings()
    assert_qwen_host(settings.DASHSCOPE_BASE_URL)
    return ChatQwen(
        model=_model_for_role(role),
        base_url=settings.DASHSCOPE_BASE_URL,
        api_key=SecretStr(settings.DASHSCOPE_API_KEY),
        timeout=settings.DASHSCOPE_TIMEOUT,
    )
