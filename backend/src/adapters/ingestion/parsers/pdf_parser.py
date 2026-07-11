from __future__ import annotations

import fitz  # PyMuPDF
from loguru import logger

from src.application.ports.outbound.publication_source import PdfTextExtractor
from src.domain.exceptions.base import IngestionError


class PyMuPdfTextExtractor(PdfTextExtractor):
    """Extract plain text from PDF bytes via PyMuPDF (fitz)."""

    def extract_text(self, data: bytes) -> str:
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # noqa: BLE001 — fitz raises a variety of errors
            raise IngestionError(f"Could not parse PDF: {exc}") from exc

        parts: list[str] = []
        try:
            for page in doc:
                try:
                    text = page.get_text().replace("\x00", "") or ""
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to extract text from a PDF page: {}", exc)
                    text = ""
                if text.strip():
                    parts.append(text)
        finally:
            doc.close()
        return "\n\n".join(parts).strip()
