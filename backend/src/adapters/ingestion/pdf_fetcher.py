from __future__ import annotations

import httpx

from src.application.ports.outbound.publication_source import PdfFetcher
from src.config import get_settings
from src.domain.exceptions.base import IngestionError


class HttpPdfFetcher(PdfFetcher):
    """Fetch PDF bytes over HTTP(S), following redirects and validating the payload."""

    async def fetch(self, url: str) -> bytes:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(
                timeout=settings.INGEST_HTTP_TIMEOUT, follow_redirects=True
            ) as client:
                resp = await client.get(
                    url, headers={"User-Agent": "Parallax/0.1 (ingestion)"}
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise IngestionError(f"Failed to fetch PDF from {url}: {exc}") from exc

        content_type = resp.headers.get("content-type", "")
        data = resp.content
        if "pdf" not in content_type.lower() and not data.startswith(b"%PDF"):
            raise IngestionError(
                f"URL did not return a PDF (content-type={content_type!r}): {url}"
            )
        return data
