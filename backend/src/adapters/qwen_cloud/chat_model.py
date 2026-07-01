from __future__ import annotations

from urllib.parse import urlparse

from langchain_qwq import ChatQwen
from pydantic import SecretStr

from src.config import get_settings
from src.domain.models.society import AgentRole

# Hosts the hackathon permits for core model traffic. Any other host is
# disqualifying, so the factory refuses to build a client pointed elsewhere.
_ALLOWED_HOSTS = frozenset(
    {
        "dashscope-intl.aliyuncs.com",  # international pay-as-you-go / workspace keys
        "dashscope.aliyuncs.com",  # domestic
        "token-plan.ap-southeast-1.maas.aliyuncs.com",  # sk-sp-* Token-Plan keys
    }
)

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


def _assert_compliant(base_url: str) -> None:
    host = urlparse(base_url).hostname or ""
    if host not in _ALLOWED_HOSTS:
        raise ValueError(
            f"Refusing to build a chat model for non-Qwen host {host!r}. "
            f"Core model calls must route through Qwen Cloud managed APIs "
            f"({', '.join(sorted(_ALLOWED_HOSTS))})."
        )


def get_chat_model(role: AgentRole | None = None) -> ChatQwen:
    """Build the LangChain chat model for a debate agent.

    Single chokepoint for constructing a Qwen chat client: reads endpoint +
    key from config only, pins the per-role model, and refuses to point at any
    non-Qwen host (hackathon compliance). The debate agents (LangGraph nodes)
    use this; embeddings/RAG stay on `QwenLLMClient`.
    """
    settings = get_settings()
    _assert_compliant(settings.DASHSCOPE_BASE_URL)
    return ChatQwen(
        model=_model_for_role(role),
        base_url=settings.DASHSCOPE_BASE_URL,
        api_key=SecretStr(settings.DASHSCOPE_API_KEY),
        timeout=settings.DASHSCOPE_TIMEOUT,
    )
