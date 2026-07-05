from __future__ import annotations

from langchain_qwq import ChatQwen
from pydantic import SecretStr

from src.adapters.qwen_cloud.compliance import assert_qwen_host
from src.adapters.qwen_cloud.token_logging import TokenUsageCallback
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
    model = _model_for_role(role)
    # Cap output per call so no single turn can run to thousands of tokens (which
    # then gets re-billed as input on every later prompt in the debate). The
    # Arbitrator's ruling needs more room than a single debate turn.
    max_tokens = (
        settings.DEBATE_MAX_ARBITER_TOKENS
        if role == AgentRole.ARBITRATOR
        else settings.DEBATE_MAX_TURN_TOKENS
    )
    return ChatQwen(
        model=model,
        base_url=settings.DASHSCOPE_BASE_URL,
        api_key=SecretStr(settings.DASHSCOPE_API_KEY),
        timeout=settings.DASHSCOPE_TIMEOUT,
        max_tokens=max_tokens,
        # Explicitly off by default: Qwen thinking mode otherwise emits a huge
        # hidden reasoning stream per turn (thousands of tokens, minutes of
        # latency) that also blows past max_tokens and breaks structured output.
        enable_thinking=settings.QWEN_DEBATE_THINKING,
        # Per-call latency + token-usage logging, tagged with the agent role.
        callbacks=[TokenUsageCallback(role.value if role else "debate", model)],
    )
