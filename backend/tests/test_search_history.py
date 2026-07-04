"""
PC2 M2 搜索历史 API 测试
"""

import uuid
import pytest
from typing import AsyncGenerator
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import SearchHistory
from app.models.user import User
from app.main import create_app
from app.core.database import get_db


def _make_user() -> User:
    uid = uuid.uuid4()
    return User(
        id=uid,
        email=f"test_{uid.hex[:8]}@test.com",
        full_name="TestUser",
        hashed_password="hashed_test_pwd",
        is_active=True,
    )


def _create_test_client(app, db_session, user):
    """配置测试 app 的依赖覆盖并返回 httpx AsyncClient"""
    from app.api.v1.deps import get_current_user

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user

    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ── 测试：基本流程 ────────────────────────────

@pytest.mark.asyncio
async def test_get_search_history_basic(client, db_session: AsyncSession):
    """获取搜索历史（基本流程）"""
    from app.core import rate_limit as rate_limit_module
    rate_limit_module._memory_bucket.clear()

    user_a = _make_user()
    db_session.add(user_a)
    await db_session.flush()

    # 写入 3 条历史（不同时间，确保降序排列可测）
    base_time = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        db_session.add(SearchHistory(
            user_id=user_a.id,
            query=f"测试查询 {i}",
            source="cnki",
            page=1,
            page_size=20,
            total_results=10 + i,
            created_at=base_time + timedelta(hours=i),
        ))
    await db_session.commit()

    app = create_app()
    async with _create_test_client(app, db_session, user_a) as ac:
        response = await ac.get("/api/v2/papers/history")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] == 3
    assert len(data["data"]["items"]) == 3
    assert data["data"]["items"][0]["query"] == "测试查询 2"
    assert data["data"]["items"][0]["source"] == "cnki"


# ── 测试：分页 ────────────────────────────────

@pytest.mark.asyncio
async def test_get_search_history_pagination(client, db_session: AsyncSession):
    """分页获取搜索历史"""
    from app.core import rate_limit as rate_limit_module
    rate_limit_module._memory_bucket.clear()

    user_a = _make_user()
    db_session.add(user_a)
    await db_session.flush()

    for i in range(25):
        db_session.add(SearchHistory(
            user_id=user_a.id,
            query=f"查询 {i:02d}",
            source="pubmed",
            page=1,
            page_size=20,
            total_results=i,
        ))
    await db_session.commit()

    app = create_app()
    async with _create_test_client(app, db_session, user_a) as ac:
        response = await ac.get("/api/v2/papers/history?limit=10&offset=0")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 25
    assert len(data["data"]["items"]) == 10
    assert data["data"]["pages"] == 3
    assert data["data"]["page"] == 1

    # 第二页
    app2 = create_app()
    async with _create_test_client(app2, db_session, user_a) as ac2:
        response2 = await ac2.get("/api/v2/papers/history?limit=10&offset=10")
    app2.dependency_overrides.clear()

    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["data"]["items"]) == 10
    assert data2["data"]["page"] == 2


# ── 测试：按 source 过滤 ──────────────────────

@pytest.mark.asyncio
async def test_get_search_history_filter_by_source(client, db_session: AsyncSession):
    """按来源过滤搜索历史"""
    from app.core import rate_limit as rate_limit_module
    rate_limit_module._memory_bucket.clear()

    user_a = _make_user()
    db_session.add(user_a)
    await db_session.flush()

    sources = ["arxiv", "pubmed", "cnki", "arxiv", "keying"]
    for i, src in enumerate(sources):
        db_session.add(SearchHistory(
            user_id=user_a.id,
            query=f"查询 {i}",
            source=src,
            page=1,
            page_size=20,
            total_results=5,
        ))
    await db_session.commit()

    app = create_app()
    async with _create_test_client(app, db_session, user_a) as ac:
        response = await ac.get("/api/v2/papers/history?source=arxiv")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    for item in data["data"]["items"]:
        assert item["source"] == "arxiv"


# ── 测试：用户隔离 ─────────────────────────────

@pytest.mark.asyncio
async def test_get_search_history_user_isolation(client, db_session: AsyncSession):
    """不同用户只能看到自己的搜索历史"""
    from app.core import rate_limit as rate_limit_module
    rate_limit_module._memory_bucket.clear()

    user_a = _make_user()
    user_b = _make_user()
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # 用户 A 的历史
    db_session.add(SearchHistory(
        user_id=user_a.id, query="A的查询", source="cnki",
        page=1, page_size=20, total_results=3,
    ))
    # 用户 B 的历史
    db_session.add(SearchHistory(
        user_id=user_b.id, query="B的查询", source="pubmed",
        page=1, page_size=20, total_results=7,
    ))
    await db_session.commit()

    app = create_app()
    async with _create_test_client(app, db_session, user_a) as ac:
        response = await ac.get("/api/v2/papers/history")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["query"] == "A的查询"
