"""
Conversation ORM 模型。

映射到 conversations 表，管理用户与 AI 的对话会话，支持置顶和语义检索。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(Base):
    """对话会话模型。

    管理用户与 AI 的对话历史，支持会话置顶、软删除和语义向量检索。

    Attributes:
        id: 会话唯一标识（UUID v4，主键）。
        user_id: 所属用户 ID（外键）。
        title: 会话标题（自动生成或用户自定义）。
        pinned: 是否置顶。
        deleted_at: 软删除时间（UTC，非空表示已删除）。
        content_vector: 会话内容语义向量（JSON，用于语义搜索）。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "conversations"

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
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    content_vector: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title!r})>"
