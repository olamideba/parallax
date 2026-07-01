from __future__ import annotations

import pytest

from src.adapters.qwen_cloud.skills.loader import list_skills, load_skill_instructions


def test_list_skills_returns_registered_skills() -> None:
    names = {s.name for s in list_skills()}
    assert names == {"claim-verification", "capacity-math"}


def test_list_skills_includes_descriptions() -> None:
    metas = {s.name: s.description for s in list_skills()}
    assert "claim" in metas["claim-verification"].lower()
    assert "capacity" in metas["capacity-math"].lower()


def test_load_skill_instructions_returns_full_procedure_body() -> None:
    body = load_skill_instructions("claim-verification")
    assert "verified" in body
    assert "refuted" in body
    assert "unclear" in body
    # Frontmatter itself must not leak into the loaded body (progressive
    # disclosure loads only the procedure, not the registry metadata).
    assert "description:" not in body


def test_load_unknown_skill_raises() -> None:
    with pytest.raises(ValueError, match="Unknown skill"):
        load_skill_instructions("does-not-exist")
