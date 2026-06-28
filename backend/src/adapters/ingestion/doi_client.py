from __future__ import annotations

from dataclasses import dataclass

import httpx
from loguru import logger

from src.application.ports.outbound.publication_source import DoiGateway, SourceMetadata
from src.config import get_settings

_UNPAYWALL_URL = "https://api.unpaywall.org/v2/{doi}"
_CROSSREF_URL = "https://api.crossref.org/works/{doi}"


@dataclass(frozen=True)
class DoiMetadata:
    doi: str
    title: str | None = None
    oa_pdf_url: str | None = None


def normalize_doi(raw: str) -> str:
    """Strip common DOI URL prefixes down to the bare DOI."""
    doi = raw.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip()


async def find_oa_pdf(doi: str) -> str | None:
    """Query Unpaywall for an open-access PDF URL; None if paywalled/unavailable."""
    settings = get_settings()
    if not settings.UNPAYWALL_EMAIL:
        logger.warning("UNPAYWALL_EMAIL unset — cannot query Unpaywall for {}", doi)
        return None
    try:
        async with httpx.AsyncClient(timeout=settings.INGEST_HTTP_TIMEOUT) as client:
            resp = await client.get(
                _UNPAYWALL_URL.format(doi=normalize_doi(doi)),
                params={"email": settings.UNPAYWALL_EMAIL},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 — OA lookup is best-effort
        logger.warning("Unpaywall lookup failed for {}: {}", doi, exc)
        return None

    best = data.get("best_oa_location") or {}
    return best.get("url_for_pdf") or None


async def fetch_metadata(doi: str) -> str | None:
    """Query Crossref for a paper's title; None on failure."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.INGEST_HTTP_TIMEOUT) as client:
            resp = await client.get(_CROSSREF_URL.format(doi=normalize_doi(doi)))
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Crossref lookup failed for {}: {}", doi, exc)
        return None

    titles = (data.get("message") or {}).get("title") or []
    return titles[0] if titles else None


async def resolve(doi: str) -> DoiMetadata:
    """Resolve a DOI to metadata + an OA PDF URL (if any)."""
    normalized = normalize_doi(doi)
    title = await fetch_metadata(normalized)
    oa_pdf_url = await find_oa_pdf(normalized)
    return DoiMetadata(doi=normalized, title=title, oa_pdf_url=oa_pdf_url)


class DoiApiGateway(DoiGateway):
    """DoiGateway backed by Unpaywall (OA PDF) + Crossref (metadata)."""

    async def resolve(self, doi: str) -> SourceMetadata:
        meta = await resolve(doi)
        return SourceMetadata(title=meta.title, pdf_url=meta.oa_pdf_url)
