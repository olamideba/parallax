import pytest
from httpx import AsyncClient


async def test_health_endpoint(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
