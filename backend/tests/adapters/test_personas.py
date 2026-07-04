from __future__ import annotations

import pytest

from src.adapters.qwen_cloud.personas import first_name


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [
        ("Dr. Jane Smith", "Jane"),
        ("Professor John Doe", "John"),
        ("Jane Smith", "Jane"),
        ("Prof. Dr. Jane Smith", "Jane"),
        ("dr. jane smith", "jane"),
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_first_name_strips_title_prefixes(display_name: str | None, expected: str | None) -> None:
    assert first_name(display_name) == expected
