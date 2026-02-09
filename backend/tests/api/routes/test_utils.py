import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.asyncio
async def test_redis_health(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/utils/redis-health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
