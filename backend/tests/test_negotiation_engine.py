import pytest
from httpx import AsyncClient

from src.domain.collaboration.negotiation_engine import NegotiationEngine


def test_negotiation_engine_instantiates():
    engine = NegotiationEngine(round_cap=3)
    assert engine.round_cap == 3


async def test_health_endpoint(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
