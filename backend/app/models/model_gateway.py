"""
ModelProvider / UserModelConfig ORM 模型。

映射到 model_providers 和 user_model_configs 表，
实现 Model Gateway 方案中的多模型提供商管理。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.core.database import Base, UniversalUUID


if TYPE_CHECKING:
    from app.models.user import User


class ModelProvider(Base):
    """模型提供商模型。

    管理系统中可用的 AI 模型提供商（OpenAI、DeepSeek、通义千问等）。

    Attributes:
        id: 提供商唯一标识（UUID v4，主键）。
        name: 内部标识名（如 "openai", "deepseek"）。
        display_name: 显示名称（如 "OpenAI", "DeepSeek"）。
        base_url: API 基础地址。
        api_type: API 类型，默认 "openai"（兼容 OpenAI 格式）。
        is_builtin: 是否为系统内置提供商（不可删除）。
        is_enabled: 是否启用。
        created_at: 创建时间（UTC）。
    """

    __tablename__ = "model_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    api_type: Mapped[str] = mapped_column(
        String(20),
        default="openai",
        server_default="openai",
    )
    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user_configs: Mapped[List["UserModelConfig"]] = relationship(
        "UserModelConfig",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ModelProvider(id={self.id}, name={self.name!r})>"


class UserModelConfig(Base):
    """用户模型配置模型。

    管理用户自定义的模型提供商 API Key 和模型选择。

    Attributes:
        id: 配置唯一标识（UUID v4，主键）。
        user_id: 所属用户 ID（外键）。
        provider_id: 模型提供商 ID（外键）。
        api_key_encrypted: 加密后的 API Key（AES-256-GCM）。
        model_name: 使用的模型名称（如 "gpt-4o", "deepseek-chat"）。
        is_default: 是否为默认配置。
        priority: 优先级（数值越大优先级越高）。
        created_at: 创建时间（UTC）。

    Note:
        (user_id, provider_id, model_name) 有唯一约束，
        同一用户对同一提供商的同一模型只能有一条配置。
    """

    __tablename__ = "user_model_configs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider_id", "model_name",
            name="uq_user_model_configs_user_provider_model",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("model_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="model_configs",
    )
    provider: Mapped["ModelProvider"] = relationship(
        "ModelProvider",
        back_populates="user_configs",
    )

    def __repr__(self) -> str:
        return f"<UserModelConfig(id={self.id}, model={self.model_name!r})>"
