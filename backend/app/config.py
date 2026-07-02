"""
FastAPI 应用配置模块。

使用 pydantic-settings 从 .env 文件和环境变量加载所有配置项。
提供全局 Settings 单例。
"""

from pathlib import Path
from functools import lru_cache

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
    DATABASE_URL: str = "sqlite+aiosqlite:///./sci_agent.db"

    # ── JWT / 认证 ───────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-a-strong-random-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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
