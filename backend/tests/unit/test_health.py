"""
健康检查端点单元测试。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient) -> None:
    """测试 GET /api/v1/health 返回 200 和 ok 状态。"""
    response = await test_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "0.1.0"
    assert "timestamp" in body["data"]


@pytest.mark.asyncio
async def test_health_db(test_client: AsyncClient) -> None:
    """测试 GET /api/v1/health/db 返回数据库连接状态。"""
    with patch(
        "app.api.v1.health.check_db_connection",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await test_client.get("/api/v1/health/db")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["database"] == "connected"
