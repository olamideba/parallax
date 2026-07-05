from __future__ import annotations

from pathlib import Path

from src.adapters.qwen_cloud.chat_model import _model_for_role, get_chat_model
from src.config import get_settings
from src.domain.models.society import AgentRole


def test_per_role_model_mapping() -> None:
    settings = get_settings()
    assert _model_for_role(AgentRole.GATEKEEPER) == settings.QWEN_MODEL_GATEKEEPER
    assert _model_for_role(AgentRole.ARBITRATOR) == settings.QWEN_MODEL_ARBITRATOR
    assert _model_for_role(AgentRole.ADVOCATE) == settings.QWEN_MODEL_DEBATE
    # None falls back to the debate model.
    assert _model_for_role(None) == settings.QWEN_MODEL_DEBATE


def test_get_chat_model_builds_qwen_client_pinned_to_dashscope() -> None:
    settings = get_settings()
    model = get_chat_model(AgentRole.ADVOCATE)
    assert "dashscope" in str(model.api_base)
    assert model.model_name == settings.QWEN_MODEL_DEBATE


def test_debate_models_disable_thinking_and_cap_output() -> None:
    """Thinking mode on a debate model emits a huge hidden reasoning stream that
    blows past max_tokens, stalls turns for minutes, and breaks structured
    output — lock it off and keep the per-turn output cap bound."""
    settings = get_settings()

    debater = get_chat_model(AgentRole.ADVOCATE)
    assert debater.enable_thinking is False
    # _is_thinking_model() is what actually gates the thinking payload + the
    # non-streaming behavior; it was silently True before we set the flag.
    assert debater._is_thinking_model() is False
    assert debater.max_tokens == settings.DEBATE_MAX_TURN_TOKENS

    arbiter = get_chat_model(AgentRole.ARBITRATOR)
    assert arbiter.enable_thinking is False
    assert arbiter.max_tokens == settings.DEBATE_MAX_ARBITER_TOKENS


def test_no_direct_chatqwen_or_openai_endpoint_in_src() -> None:
    """Prove the factory is the only place that builds a Qwen chat client and
    that no non-Qwen endpoint is hardcoded anywhere in src/."""
    src = Path(__file__).resolve().parents[2] / "src"
    factory = src / "adapters" / "qwen_cloud" / "chat_model.py"
    offenders_construct: list[str] = []
    offenders_openai: list[str] = []
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "api.openai.com" in text:
            offenders_openai.append(str(path))
        if path != factory and ("ChatQwen(" in text or "ChatOpenAI(" in text):
            offenders_construct.append(str(path))
    assert not offenders_openai, f"Hardcoded OpenAI endpoint in: {offenders_openai}"
    assert not offenders_construct, (
        f"Chat model constructed outside get_chat_model factory in: {offenders_construct}"
    )
