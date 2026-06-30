from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    """Blob storage for uploaded files (PDFs, CVs) addressed by an opaque key."""

    @abstractmethod
    async def download(self, storage_key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def upload(
        self, storage_key: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        raise NotImplementedError
