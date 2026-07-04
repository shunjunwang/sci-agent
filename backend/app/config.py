"""
FastAPI 应用配置模块。

使用 pydantic-settings 从 .env 文件和环境变量加载所有配置项。
提供全局 Settings 单例。
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，所有配置项从 .env 文件或环境变量读取。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── 数据库 ────────────────────────────────────────
    # 默认 SQLite 仅用于开发环境，生产环境需通过环境变量覆盖为 PostgreSQL 连接字符串
    DATABASE_URL: str = "sqlite+aiosqlite:///./sci_agent.db"

    # ── JWT / 认证 ───────────────────────────────────
    SECRET_KEY: Optional[str] = Field(None, min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── M1: 用户认证 ─────────────────────────────────
    AUTH_VERIFY_EMAIL: bool = False           # 是否要求邮箱验证
    AUTH_REQUIRE_CONFIRMATION: bool = False   # 注册后是否需要管理员确认
    AUTH_PASSWORD_MIN_LENGTH: int = 8         # 密码最小长度
    AUTH_LOCKOUT_MAX_ATTEMPTS: int = 5        # 登录失败锁定阈值
    AUTH_LOCKOUT_DURATION_MINUTES: int = 15   # 锁定持续时间

    # ── CORS ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── 应用 ─────────────────────────────────────────
    APP_NAME: str = "SciAgent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENV: str = "dev"

    # ── 请求限制 ─────────────────────────────────────
    MAX_REQUEST_BODY_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # ── Model Gateway ───────────────────────────────
    ENCRYPTION_KEY: str = ""
    DEFAULT_MODEL_TIMEOUT: int = 60
    MAX_MODEL_TOKENS: int = 4096

    # ── 缓存 (PC2 M2) ────────────────────────────────
    CACHE_TYPE: str = "memory"  # memory / redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 秒

    # ── 科应 keying-cli 认证 (PC2 M2) ────────────────
    SCIENCERIVER_APP_ID: str = ""
    SCIENCERIVER_APP_SECRET: str = ""

    # ── 外部 API (PC2 M2) ────────────────────────────
    KEYING_API_BASE: str = "https://api.keying.com/v1"
    KEYING_API_KEY: str = ""

    ARXIV_API_BASE: str = "https://export.arxiv.org/api/query"
    PUBMED_API_BASE: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    CNKI_API_BASE: str = "https://api.cnki.net/v1"

    # ── 限流 (PC2 M2) ────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BACKEND: str = "memory"   # memory / redis
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_LOGIN_BURST: int = 10
    RATE_LIMIT_API_PER_MINUTE: int = 60
    RATE_LIMIT_API_BURST: int = 120

    # ── 加密后端 ─────────────────────────────────
    ENCRYPTION_BACKEND: str = "fernet"   # fernet / aes256gcm

    # ── M2: 文献检索（统一命名别名）──────────────────
    SEARCH_DEFAULT_SOURCES: str = "arxiv,keying,pubmed"  # 默认启用的检索源
    SEARCH_TIMEOUT_SECONDS: int = 30                     # 单次检索超时
    SEARCH_MAX_RESULTS_PER_SOURCE: int = 20              # 每个源最大返回数

    # ── M3: 个人知识库 ───────────────────────────────
    KNOWLEDGE_SEARCH_BACKEND: str = "sqlite"        # 全文搜索后端: sqlite / elasticsearch
    KNOWLEDGE_DEFAULT_CITATION_STYLE: str = "gbt7714"   # 默认引用格式
    KNOWLEDGE_READING_HISTORY_DAYS: int = 30        # 阅读历史保留天数

    # ── M6 Docker仿真沙箱 ───────────────────────────
    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    DOCKER_API_VERSION: str = "auto"
    DOCKER_DEFAULT_IMAGE: str = "sci-agent/sandbox:latest"
    M6_SANDBOX_CPU_LIMIT: float = 2.0
    M6_SANDBOX_MEMORY_LIMIT_MB: int = 2048
    M6_SANDBOX_TIMEOUT_SECONDS: int = 300

    # ── M7 协作空间 ─────────────────────────────────
    M7_INVITATION_EXPIRE_DAYS: int = 7

    # ── M5 AI写作辅助 ───────────────────────────────
    WRITING_DEFAULT_STYLE: str = "academic"
    WRITING_MAX_PAPERS: int = 50
    WRITING_LLM_MODEL: str = "gpt-4o"

    # ── M8 防篡改日志 ───────────────────────────────
    M8_HASH_CHAIN_SALT: Optional[str] = Field(None)

    # ── M9 算法商城 ─────────────────────────────────
    ALGORITHM_MAX_EXECUTION_TIME: int = 3600
    ALGORITHM_DEFAULT_CPU_LIMIT: str = "1.0"
    ALGORITHM_DEFAULT_MEMORY_LIMIT: str = "512m"

    @property
    def is_production(self) -> bool:
        """判断是否为生产环境。"""
        return self.ENV == "prod"

    @property
    def is_development(self) -> bool:
        """判断是否为开发环境。"""
        return self.ENV == "dev"

    @property
    def project_root(self) -> Path:
        """返回项目根目录路径。"""
        return Path(__file__).resolve().parent.parent.parent


@lru_cache
def get_settings() -> Settings:
    """返回缓存的 Settings 单例。

    Returns:
        Settings: 全局配置实例。
    """
    return Settings()


settings = get_settings()


def load_env_to_os():
    """将配置注入 os.environ（keying-cli 等外部工具通过 os.environ 读取）。"""
    env_mappings = {
        "SCIENCERIVER_APP_ID": settings.SCIENCERIVER_APP_ID,
        "SCIENCERIVER_APP_SECRET": settings.SCIENCERIVER_APP_SECRET,
    }
    for key, value in env_mappings.items():
        if value and key not in os.environ:
            os.environ[key] = value
