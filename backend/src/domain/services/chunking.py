from __future__ import annotations

import re

# Character-based chunking. ~1 token ≈ 4 chars, so ~2000 chars ≈ 500 tokens —
# comfortably within embedding model context while keeping chunks semantically dense.
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_OVERLAP = 200

_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Collapse runaway whitespace produced by PDF extraction."""
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split text into overlapping character windows.

    Prefers to break on a paragraph/sentence boundary near the window edge so
    chunks don't split mid-word. Empty or whitespace-only chunks are dropped.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            # Try to break on a natural boundary within the last 20% of the window.
            window = text[start:end]
            boundary = _last_boundary(window, int(chunk_size * 0.8))
            if boundary != -1:
                end = start + boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break
        start = max(end - overlap, start + 1)

    return chunks


def _last_boundary(window: str, min_index: int) -> int:
    """Return index just past the best break point (paragraph > sentence > space)."""
    for marker in ("\n\n", ". ", "\n", " "):
        idx = window.rfind(marker)
        if idx >= min_index:
            return idx + len(marker)
    return -1
