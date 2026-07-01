from __future__ import annotations

from pathlib import Path

import pytest

from src.adapters.qwen_cloud.chat_model import (
    _assert_compliant,
    _model_for_role,
    get_chat_model,
)
from src.config import get_settings
from src.domain.models.society import AgentRole


def test_per_role_model_mapping() -> None:
    settings = get_settings()
    assert _model_for_role(AgentRole.GATEKEEPER) == settings.QWEN_MODEL_GATEKEEPER
    assert _model_for_role(AgentRole.ARBITRATOR) == settings.QWEN_MODEL_ARBITRATOR
    assert _model_for_role(AgentRole.ADVOCATE) == settings.QWEN_MODEL_DEBATE
    # None falls back to the debate model.
    assert _model_for_role(None) == settings.QWEN_MODEL_DEBATE


def test_compliance_guard_rejects_non_qwen_host() -> None:
    with pytest.raises(ValueError, match="non-Qwen host"):
        _assert_compliant("https://api.openai.com/v1")


def test_compliance_guard_accepts_dashscope_hosts() -> None:
    # Must not raise for any permitted Qwen Cloud host.
    _assert_compliant("https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    _assert_compliant("https://dashscope.aliyuncs.com/compatible-mode/v1")
    _assert_compliant(
        "https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    )


def test_get_chat_model_builds_qwen_client_pinned_to_dashscope() -> None:
    settings = get_settings()
    model = get_chat_model(AgentRole.ADVOCATE)
    assert "dashscope" in str(model.api_base)
    assert model.model_name == settings.QWEN_MODEL_DEBATE


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
