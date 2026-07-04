"""
数据库模块 — SQLAlchemy 2.0 异步引擎。

使用 aiosqlite 驱动连接 SQLite / asyncpg 驱动连接 PostgreSQL，
提供连接池管理和依赖注入函数。
提供跨数据库的 UUID 类型兼容层（PostgreSQL native UUID → SQLite CHAR(36)）。
"""

import uuid
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import String, types
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ── 跨数据库 UUID 类型 ───────────────────────────────

class UniversalUUID(types.TypeDecorator):
    """兼容 PostgreSQL 和 SQLite 的 UUID 类型。

    PostgreSQL → native UUID
    SQLite     → CHAR(36)
    """
    impl = types.CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        elif dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return uuid.UUID(str(value))


# ── 连接池参数：区分 SQLite 和 PostgreSQL ───────────

_is_postgresql = settings.DATABASE_URL.startswith("postgresql")

if _is_postgresql:
    engine_kwargs: dict[str, Any] = {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
else:
    # SQLite：不适用 pool_size/max_overflow，仅启连接探活
    engine_kwargs = {
        "pool_pre_ping": True,
        "connect_args": {"check_same_thread": False},
    }


# ── 异步引擎 ─────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **engine_kwargs,
)

# ── 会话工厂 ─────────────────────────────────────────
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# PC2 兼容别名
AsyncSessionLocal = async_session_factory


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。

    所有 ORM 模型需继承此类。
    """

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：提供数据库会话。

    每个请求获取一个独立会话，请求结束后自动关闭。
    遇 OperationalError 时尝试 1 次重连。

    Yields:
        AsyncSession: 数据库异步会话实例。

    Example:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    max_retries = 1
    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            async with async_session_factory() as session:
                yield session
                await session.commit()
                return
        except OperationalError as e:
            last_exc = e
            if attempt < max_retries:
                continue
            raise
        except Exception:
            raise

    if last_exc:
        raise last_exc


async def check_db_connection() -> bool:
    """检查数据库连接是否正常。

    Returns:
        bool: 连接成功返回 True，否则 False。
    """
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """释放数据库引擎连接池。"""
    await engine.dispose()


async def init_db() -> None:
    """初始化数据库（创建所有表）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
