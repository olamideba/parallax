from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET

import httpx
from loguru import logger

from src.application.ports.outbound.publication_source import ArxivGateway, SourceMetadata
from src.config import get_settings
from src.domain.exceptions.base import IngestionError

_ABS_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(?P<id>[^\s?#]+?)(?:v\d+)?(?:\.pdf)?$", re.IGNORECASE)
_API_URL = "https://export.arxiv.org/api/query"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass(frozen=True)
class ArxivMetadata:
    arxiv_id: str
    title: str | None
    pdf_url: str


def parse_arxiv_id(url: str) -> str | None:
    """Extract the bare arXiv id from an abs/ or pdf/ URL."""
    if not url:
        return None
    match = _ABS_RE.search(url.strip())
    if not match:
        return None
    return match.group("id")


def is_arxiv_url(url: str | None) -> bool:
    return url is not None and "arxiv.org" in url.lower()


def pdf_url_for(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


async def fetch_metadata(arxiv_id: str) -> ArxivMetadata:
    """Query the arXiv API for a paper's metadata; falls back to id-only on error."""
    settings = get_settings()
    title: str | None = None
    try:
        async with httpx.AsyncClient(timeout=settings.INGEST_HTTP_TIMEOUT) as client:
            resp = await client.get(_API_URL, params={"id_list": arxiv_id, "max_results": 1})
            resp.raise_for_status()
        root = ET.fromstring(resp.text)
        entry = root.find("atom:entry", _ATOM_NS)
        if entry is not None:
            title_el = entry.find("atom:title", _ATOM_NS)
            if title_el is not None and title_el.text:
                title = re.sub(r"\s+", " ", title_el.text).strip()
    except Exception as exc:  # noqa: BLE001 — metadata is best-effort
        logger.warning("arXiv metadata lookup failed for {}: {}", arxiv_id, exc)

    return ArxivMetadata(arxiv_id=arxiv_id, title=title, pdf_url=pdf_url_for(arxiv_id))


class ArxivApiGateway(ArxivGateway):
    """ArxivGateway backed by the public arXiv export API."""

    def is_arxiv_url(self, url: str | None) -> bool:
        return is_arxiv_url(url)

    async def resolve(self, url: str) -> SourceMetadata:
        arxiv_id = parse_arxiv_id(url)
        if not arxiv_id:
            raise IngestionError(f"Could not parse arXiv id from {url}")
        meta = await fetch_metadata(arxiv_id)
        return SourceMetadata(title=meta.title, pdf_url=meta.pdf_url)
