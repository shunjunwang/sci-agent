"""
PC2 M2 数据源 API 测试
"""

import pytest


@pytest.mark.asyncio
async def test_list_sources(client):
    """测试数据源列表"""
    response = await client.get("/api/v2/sources")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    sources = data["data"]["sources"]
    assert len(sources) == 4
    source_ids = [s["id"] for s in sources]
    assert "arxiv" in source_ids
    assert "pubmed" in source_ids
    assert "cnki" in source_ids
    assert "keying" in source_ids
