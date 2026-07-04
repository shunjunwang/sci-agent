"""
Alembic 环境配置。

从应用 Settings 读取 DATABASE_URL，并连接 models.Base.metadata
以实现自动迁移检测。
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.core.database import Base

# 导入所有模型以确保 metadata 包含全部表定义
from app.models import activity, annotation, billing, conversation, document, library, model_gateway, paper, sandbox, token_blacklist, user, workspace  # noqa: F401

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 target_metadata 指向 ORM Base
target_metadata = Base.metadata

# 将异步数据库 URL 转换为同步版本（仅 SQLite 需要）
db_url = settings.DATABASE_URL
if "aiosqlite" in db_url:
    db_url = db_url.replace("aiosqlite", "sqlite")
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """以 "离线" 模式运行迁移 — 生成 SQL 脚本而不连接数据库。

    配置 context 使用 URL 和 literal SQL 编译模式。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """以 "在线" 模式运行迁移 — 连接数据库并执行。

    从 config 创建 Engine 并关联 connection 到 context。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
