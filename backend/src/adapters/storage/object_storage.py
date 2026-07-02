from __future__ import annotations

from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from loguru import logger

from src.application.ports.outbound.object_storage import ObjectStorage
from src.config import get_settings
from src.domain.exceptions.base import IngestionError, NotFoundError


@asynccontextmanager
async def _r2_client():
    settings = get_settings()
    if not (
        settings.R2_ENDPOINT_URL
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
    ):
        raise IngestionError("R2 storage is not configured")

    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    ) as client:
        yield client, settings.R2_BUCKET


class R2ObjectStorage(ObjectStorage):
    """Cloudflare R2 (S3-compatible) blob storage."""

    async def download(self, storage_key: str) -> bytes:
        async with _r2_client() as (client, bucket):
            logger.debug("Downloading {} from bucket {}", storage_key, bucket)
            try:
                resp = await client.get_object(Bucket=bucket, Key=storage_key)
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code")
                if code in ("NoSuchKey", "404", "NotFound"):
                    raise NotFoundError(f"Object {storage_key} not found in storage") from exc
                raise
            async with resp["Body"] as stream:
                return await stream.read()

    async def upload(
        self, storage_key: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        async with _r2_client() as (client, bucket):
            await client.put_object(
                Bucket=bucket, Key=storage_key, Body=data, ContentType=content_type
            )
        return storage_key
