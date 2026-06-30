import pytest

from src.adapters.ingestion import doi_client


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
