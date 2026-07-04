"""
Annotation ORM 模型。

映射到 annotations 表，存储用户对文献的批注/高亮内容。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.paper import Paper
    from app.models.user import User


class Annotation(Base):
    """文献批注模型。

    存储用户在阅读文献时添加的高亮区域和批注笔记。

    Attributes:
        id: 批注唯一标识（UUID v4，主键）。
        user_id: 创建用户 ID（外键）。
        paper_id: 所属文献 ID（外键）。
        content: 批注文本内容。
        highlight_range: 高亮区域位置信息（JSON，如 {"start": 0, "end": 50, "page": 3}）。
        color: 高亮颜色，默认黄色。
        is_public: 是否公开（协作空间中可见）。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "annotations"

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
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    highlight_range: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    color: Mapped[str] = mapped_column(
        String(20),
        default="#FFEB3B",
        server_default="#FFEB3B",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
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
        back_populates="annotations",
    )
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="annotations",
    )

    def __repr__(self) -> str:
        return f"<Annotation(id={self.id}, paper_id={self.paper_id})>"
