from __future__ import annotations

from jinja2 import Environment, PackageLoader

# Agent prompts live as Jinja templates in this package's `prompts/` dir so
# they can be iterated without touching Python. autoescape stays off — these
# render into LLM prompts, not HTML.
_env = Environment(
    loader=PackageLoader("src.adapters.qwen_cloud", "prompts"),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(name: str, **context: object) -> str:
    """Render an agent prompt template (e.g. ``gatekeeper.j2``)."""
    return _env.get_template(name).render(**context)
