from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceMetadata:
    """What an external resolver can tell us about a publication.

    `pdf_url` is None when no retrievable open-access PDF exists (e.g. a
    paywalled DOI) — the caller should then fall back to manual upload.
    """

    title: str | None = None
    pdf_url: str | None = None


class PdfFetcher(ABC):
    """Fetch a PDF document's raw bytes from an HTTP(S) URL."""

    @abstractmethod
    async def fetch(self, url: str) -> bytes:
        raise NotImplementedError


class PdfTextExtractor(ABC):
    """Extract plain text from PDF bytes."""

    @abstractmethod
    def extract_text(self, data: bytes) -> str:
        raise NotImplementedError


class ArxivGateway(ABC):
    """Resolve arXiv URLs to a downloadable PDF + metadata."""

    @abstractmethod
    def is_arxiv_url(self, url: str | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def resolve(self, url: str) -> SourceMetadata:
        raise NotImplementedError


class DoiGateway(ABC):
    """Resolve a DOI to an open-access PDF (if any) + metadata."""

    @abstractmethod
    async def resolve(self, doi: str) -> SourceMetadata:
        raise NotImplementedError
