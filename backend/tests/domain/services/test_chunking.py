import pytest

from src.domain.services.chunking import chunk_text, normalize_text


def test_normalize_collapses_whitespace():
    assert normalize_text("a    b\t\tc") == "a b c"
    assert normalize_text("x\n\n\n\n\ny") == "x\n\ny"


def test_short_text_single_chunk():
    assert chunk_text("hello world", chunk_size=100, overlap=10) == ["hello world"]


def test_empty_text_no_chunks():
    assert chunk_text("   \n\n  ", chunk_size=100, overlap=10) == []


def test_chunking_overlaps_and_covers():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    assert all(c.strip() for c in chunks)


def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)
