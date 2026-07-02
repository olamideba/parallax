from __future__ import annotations

from urllib.parse import urlparse

# Hosts the hackathon permits for core model traffic. Any other host is
# disqualifying, so every Qwen Cloud adapter (chat, rerank, ...) routes through
# this one check before making a request.
_ALLOWED_HOSTS = frozenset(
    {
        "dashscope-intl.aliyuncs.com",  # international pay-as-you-go / workspace keys
        "dashscope.aliyuncs.com",  # domestic
        "token-plan.ap-southeast-1.maas.aliyuncs.com",  # sk-sp-* Token-Plan keys
    }
)
# Workspace-scoped hosts (e.g. qwen3-rerank: `{workspace_id}.ap-southeast-1.
# maas.aliyuncs.com`) vary per account, so they're matched by suffix instead of
# an exact-host allowlist entry. Still Alibaba's own domain — not a loophole.
_ALLOWED_SUFFIXES = (".maas.aliyuncs.com",)


def assert_qwen_host(base_url: str) -> None:
    """Refuse to build a client pointed at any non-Qwen-Cloud host."""
    host = urlparse(base_url).hostname or ""
    if host in _ALLOWED_HOSTS or host.endswith(_ALLOWED_SUFFIXES):
        return
    raise ValueError(
        f"Refusing to call non-Qwen host {host!r}. Core model calls must route "
        f"through Qwen Cloud managed APIs."
    )
