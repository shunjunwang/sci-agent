"""
PC2 M2 健康检查测试
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """测试健康检查端点"""
    response = await client.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["service"] == "paper-search"
    assert data["data"]["version"] == "0.2.0"
