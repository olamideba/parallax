import pytest

from src.adapters.ingestion import arxiv_client


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
