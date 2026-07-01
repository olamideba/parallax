from __future__ import annotations

import pytest

from src.adapters.qwen_cloud.compliance import assert_qwen_host


def test_rejects_non_qwen_host() -> None:
    with pytest.raises(ValueError, match="non-Qwen host"):
        assert_qwen_host("https://api.openai.com/v1")


def test_accepts_exact_dashscope_hosts() -> None:
    assert_qwen_host("https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    assert_qwen_host("https://dashscope.aliyuncs.com/compatible-mode/v1")
    assert_qwen_host("https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1")


def test_accepts_workspace_scoped_maas_hosts() -> None:
    # Rerank hosts are per-workspace subdomains of the same Alibaba domain.
    assert_qwen_host("https://ws-s428v3m88m8hgcx2.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/reranks")
    assert_qwen_host("https://some-other-workspace.cn-beijing.maas.aliyuncs.com/api/v1")


def test_rejects_lookalike_host() -> None:
    with pytest.raises(ValueError, match="non-Qwen host"):
        assert_qwen_host("https://dashscope-intl.aliyuncs.com.evil.com/v1")
