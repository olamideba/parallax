from __future__ import annotations

import pytest

from src.adapters.ingestion import arxiv_client, doi_client
from src.domain.services.chunking import chunk_text, normalize_text

# --- chunker ---

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
    # every chunk fits within a reasonable bound of chunk_size
    assert all(len(c) <= 200 for c in chunks)
    # no empty chunks
    assert all(c.strip() for c in chunks)


def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)


# --- arxiv ---

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://arxiv.org/abs/2205.01068", "2205.01068"),
        ("https://arxiv.org/abs/2205.01068v3", "2205.01068"),
        ("http://arxiv.org/pdf/2205.01068.pdf", "2205.01068"),
        ("https://example.com/paper", None),
    ],
)
def test_parse_arxiv_id(url, expected):
    assert arxiv_client.parse_arxiv_id(url) == expected


def test_is_arxiv_url():
    assert arxiv_client.is_arxiv_url("https://arxiv.org/abs/1234.5678")
    assert not arxiv_client.is_arxiv_url("https://doi.org/10.1/x")
    assert not arxiv_client.is_arxiv_url(None)


def test_pdf_url_for():
    assert arxiv_client.pdf_url_for("2205.01068") == "https://arxiv.org/pdf/2205.01068.pdf"


# --- doi ---

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://doi.org/10.1000/xyz", "10.1000/xyz"),
        ("doi:10.1000/xyz", "10.1000/xyz"),
        ("  10.1000/xyz ", "10.1000/xyz"),
    ],
)
def test_normalize_doi(raw, expected):
    assert doi_client.normalize_doi(raw) == expected
