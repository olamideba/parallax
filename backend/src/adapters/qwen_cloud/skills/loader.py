from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_SKILLS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class SkillMeta:
    name: str
    description: str


def _parse_skill_file(text: str) -> tuple[dict[str, str], str]:
    """Split a SKILL.md into its `---`-delimited frontmatter and body.

    Frontmatter here is flat `key: value` lines, not full YAML — the two
    fields we need (name, description) never contain colons or nesting.
    """
    if not text.startswith("---"):
        return {}, text.strip()
    _, frontmatter, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in frontmatter.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.strip()


def _skill_files() -> list[Path]:
    return sorted(_SKILLS_DIR.glob("*/SKILL.md"))


def list_skills() -> list[SkillMeta]:
    """Registry-only view (name + description) — cheap, used to advertise
    what's available without loading full instructions into context."""
    metas = []
    for skill_file in _skill_files():
        meta, _ = _parse_skill_file(skill_file.read_text(encoding="utf-8"))
        metas.append(
            SkillMeta(
                name=meta.get("name", skill_file.parent.name),
                description=meta.get("description", ""),
            )
        )
    return metas


def load_skill_instructions(name: str) -> str:
    """Progressive disclosure: the full procedure body is only read from disk
    and injected into a prompt when a tool actually invokes this skill."""
    for skill_file in _skill_files():
        meta, body = _parse_skill_file(skill_file.read_text(encoding="utf-8"))
        if meta.get("name") == name:
            return body
    raise ValueError(f"Unknown skill: {name!r}")
