from __future__ import annotations

import pytest

from src.adapters.qwen_cloud.tools import claim_verification as cv_module
from src.adapters.qwen_cloud.tools.claim_verification import ClaimVerdict, verify_claim


class _FakeStructuredModel:
    def __init__(self, result: ClaimVerdict) -> None:
        self._result = result
        self.last_prompt: str | None = None

    async def ainvoke(self, prompt: str) -> ClaimVerdict:
        self.last_prompt = prompt
        return self._result


class _FakeChatModel:
    def __init__(self, result: ClaimVerdict) -> None:
        self._structured = _FakeStructuredModel(result)

    def with_structured_output(self, schema):  # noqa: ANN001, ARG002
        return self._structured


@pytest.mark.asyncio
async def test_verify_claim_returns_verdict_from_model(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = ClaimVerdict(verdict="verified", receipt="chunk X", reasoning="matches directly")
    fake = _FakeChatModel(expected)
    monkeypatch.setattr(cv_module, "get_chat_model", lambda role=None: fake)

    result = await verify_claim("I published at NeurIPS", ["chunk X mentions NeurIPS paper"])

    assert result == expected
    assert "I published at NeurIPS" in fake._structured.last_prompt
    assert "chunk X mentions NeurIPS paper" in fake._structured.last_prompt


@pytest.mark.asyncio
async def test_verify_claim_handles_no_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = ClaimVerdict(verdict="unclear", reasoning="no evidence retrieved")
    fake = _FakeChatModel(expected)
    monkeypatch.setattr(cv_module, "get_chat_model", lambda role=None: fake)

    result = await verify_claim("I built a rocket", [])

    assert result.verdict == "unclear"
    assert "no evidence retrieved" in fake._structured.last_prompt.lower()


@pytest.mark.asyncio
async def test_claim_verification_tool_invokable(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = ClaimVerdict(verdict="refuted", receipt="chunk Y", reasoning="contradicts")
    fake = _FakeChatModel(expected)
    monkeypatch.setattr(cv_module, "get_chat_model", lambda role=None: fake)

    result = await cv_module.claim_verification_tool.ainvoke(
        {"claim": "I am the sole author", "evidence_chunks": ["chunk Y lists co-authors"]}
    )

    assert result["verdict"] == "refuted"
