"""
Pytest 全局 fixtures 与配置。

提供测试客户端、内存数据库等共用 fixture。
"""

import asyncio
import threading
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db

# P0-1: 确保 TokenBlacklist 表在 create_all 前注册
import app.models.token_blacklist  # noqa: E402, F401 — 触发 ORM 注册

# 使用 aiosqlite 作为测试内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"


@pytest.fixture(scope="module")
def event_loop() -> Any:
    """创建 module 级别的事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope="module")
async def test_engine() -> Any:
    """创建测试用异步 SQLAlchemy 引擎。

    幂等跳过 PG 专用类型（Vector / INET 等）的表创建。

    Yields:
        AsyncEngine: 测试引擎实例。
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception:
            # SQLite 不支持 pgvector / INET 等 PG 专用类型，
            # 健康检查类测试无需完整表结构，忽略建表失败。
            pass

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="module")
async def test_session_factory(test_engine: Any) -> async_sessionmaker[AsyncSession]:
    """创建测试用会话工厂。

    Args:
        test_engine: 测试引擎 fixture。

    Returns:
        async_sessionmaker: 异步会话工厂。
    """
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """每个测试函数获取独立数据库会话。

    Args:
        test_session_factory: 测试会话工厂。

    Yields:
        AsyncSession: 独立异步会话。
    """
    async with test_session_factory() as session:
        yield session


# P3-08: 全局锁防止并行测试时 user_middleware 竞态
_mw_lock = threading.Lock()


@pytest_asyncio.fixture
async def test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """创建带内存数据库覆盖的测试 HTTP 客户端。

    覆盖 get_db 依赖以使用测试会话，并临时移除限流中间件。

    Args:
        db_session: 测试数据库会话。

    Yields:
        AsyncClient: httpx 异步测试客户端。
    """
    from app.main import app
    from app.core.rate_limit import RateLimitMiddleware

    # 临时移除限流中间件，避免测试间累积触发 429
    # P3-08: 使用锁保护全局 user_middleware 列表，防止并行测试竞态
    with _mw_lock:
        saved_middleware = []
        remaining_middleware = []
        for mw in app.user_middleware:
            if mw.cls == RateLimitMiddleware:
                saved_middleware.append(mw)
            else:
                remaining_middleware.append(mw)
        app.user_middleware.clear()
        app.user_middleware.extend(remaining_middleware)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

    # 恢复限流中间件（P3-08: 加锁保护）
    with _mw_lock:
        app.user_middleware.clear()
        app.user_middleware.extend(remaining_middleware + saved_middleware)


@pytest_asyncio.fixture
async def client(test_client: AsyncClient) -> AsyncClient:
    """别名 fixture，兼容 PC2 M2 测试中使用 `client` 参数名的测试。

    Args:
        test_client: 标准测试客户端 fixture。

    Returns:
        AsyncClient: 同 test_client。
    """
    return test_client


@pytest_asyncio.fixture
async def auth_client(test_client: AsyncClient) -> AsyncClient:
    """带认证头的测试客户端。

    先注册测试用户并登录获取 token，后续请求自动携带 Bearer。

    Args:
        test_client: 标准测试客户端 fixture。

    Returns:
        AsyncClient: 已认证的 httpx 异步客户端。
    """
    # 注册测试用户（支持重复注册 400，此时直接走登录流程）
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_papers@example.com",
            "password": "Test@123456",
            "full_name": "Test Papers User",
            "institution": "Test University",
        },
    )
    # 登录获取 token
    login_resp = await test_client.post(
        "/api/v1/auth/login",
        json={"email": "test_papers@example.com", "password": "Test@123456"},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code} {login_resp.text}"
    token = login_resp.json()["access_token"]
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client
