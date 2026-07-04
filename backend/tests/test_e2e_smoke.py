"""
P4-09: 最小 E2E 冒烟测试

覆盖核心链路：注册 → 登录 → 获取 token → 调用 /api/v2/papers/search → 验证响应格式。
不依赖外部 API，使用科应 mock 数据。
"""

import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

MOCK_SEARCH_RESULT = [{
    "srid": "SR-E2E-001",
    "originalTitle": "Advances in AI Testing",
    "chineseTitle": "AI 测试进展",
    "originalAuthors": ["Test Author"],
    "chineseAbstract": "自动化测试技术与方法综述",
    "publicationDate": "2026-01-01",
    "doi": "10.9999/e2e",
    "dataSource": "arXiv",
    "featuredTags": [],
    "hasPdf": False,
    "docType": "papers",
}]


@pytest.mark.asyncio
async def test_e2e_register_login_search(test_client: AsyncClient):
    """E2E: 注册 → 登录 → 搜索文献 → 验证响应"""
    c = test_client
    uid = uuid.uuid4().hex[:8]
    email = f"e2e-{uid}@smoketest.com"
    password = "SmokeTest@2026!"

    # Step 1: 注册
    resp = await c.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": f"E2E User {uid}",
        "password": password,
        "institution": "Smoke University",
    })
    assert resp.status_code in (201, 400), \
        f"Register: expected 201/400, got {resp.status_code}: {resp.text}"
    user_data = resp.json()
    assert "id" in user_data, f"Register response missing id: {user_data}"

    # Step 2: 登录
    resp = await c.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert resp.status_code == 200, \
        f"Login: expected 200, got {resp.status_code}: {resp.text}"
    token_data = resp.json()
    assert "access_token" in token_data, \
        f"Login response missing access_token: {token_data}"
    token = token_data["access_token"]

    # Step 3: 带认证头调用搜索（mock 科应）
    auth_headers = {"Authorization": f"Bearer {token}"}
    mock_client = MagicMock()
    mock_client.search.return_value = (MOCK_SEARCH_RESULT, 1)

    with patch(
        "app.services.keying_service.KeyingService._get_client",
        return_value=mock_client,
    ):
        resp = await c.get(
            "/api/v2/papers/search",
            params={"q": "AI testing", "source": "keying"},
            headers=auth_headers,
        )

    # Step 4: 验证响应格式
    assert resp.status_code == 200, \
        f"Search: expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    # 响应体结构验证（v2 API 使用 code=0 表示成功）
    assert data["code"] == 0, f"code mismatch: {data}"
    assert data["data"]["total"] >= 0
    assert data["data"]["query"] == "AI testing"
    assert "results" in data["data"]
