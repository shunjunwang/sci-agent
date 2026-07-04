"""
Pytest 全局 fixtures 与配置。

提供测试客户端、内存数据库等共用 fixture。
"""

import asyncio
import os
import threading
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

# ── 环境修复：确保 .env 从 backend/ 目录加载 ─────────────────
# pytest 可能从项目根目录运行，导致 pydantic-settings 找不到 backend/.env。
# 读取 .env 中 SECRET_KEY 并注入环境变量，确保 JWT 签名可用。
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            if key and key not in os.environ:  # 不覆盖已有环境变量
                # 移除引号
                val = val.strip().strip('"').strip("'")
                os.environ[key] = val

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db  # noqa: E402

# P0-1: 确保 TokenBlacklist 表在 create_all 前注册
import app.models.token_blacklist  # noqa: E402, F401 — 触发 ORM 注册

# P3-07: 确保所有 ORM 模型在 create_all 前注册，解决 security/performance 测试
# 因 create_all 早于 app.main 导入导致部分表缺失的问题。
import app.models  # noqa: E402, F401

# 使用文件型 SQLite 作为测试数据库（:memory: 在 aiosqlite 中存在 per-connection 隔离问题）
_TEST_DB_PATH = Path(__file__).resolve().parent / "test_sci_agent.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_TEST_DB_PATH.as_posix()}"


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
    # 确保所有 ORM 模型已注册到 Base.metadata 再建表
    import app.models  # noqa: E402, F811 — 触发所有模型导入

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

    # 清理测试数据库文件
    if _TEST_DB_PATH.exists():
        try:
            _TEST_DB_PATH.unlink()
        except OSError:
            pass  # 文件可能被其他进程锁定，忽略


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
