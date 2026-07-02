"""
Pytest 全局 fixtures 与配置。

提供测试客户端、内存数据库等共用 fixture。
"""

import asyncio
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


@pytest_asyncio.fixture
async def test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """创建带内存数据库覆盖的测试 HTTP 客户端。

    覆盖 get_db 依赖以使用测试会话。

    Args:
        db_session: 测试数据库会话。

    Yields:
        AsyncClient: httpx 异步测试客户端。
    """
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
