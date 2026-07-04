"""
UserLibrary ORM 模型。

映射到 user_library 表，管理用户个人知识库中的文献收藏。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.core.database import Base, UniversalUUID


if TYPE_CHECKING:
    from app.models.paper import Paper
    from app.models.user import User


class UserLibrary(Base):
    """用户知识库模型。

    管理用户收藏的文献，支持文件夹、标签、收藏/已读状态。

    Attributes:
        id: 记录唯一标识（UUID v4，主键）。
        user_id: 用户 ID（外键）。
        paper_id: 文献 ID（外键）。
        folder_name: 所属文件夹名称。
        tags: 标签数组。
        is_favorite: 是否收藏。
        is_read: 是否已读。
        added_at: 添加时间（UTC）。

    Note:
        (user_id, paper_id) 有唯一约束，同一用户不可重复添加同一文献。
    """

    __tablename__ = "user_library"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_library_user_paper"),
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
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    folder_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_library",
    )
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="user_library",
    )

    def __repr__(self) -> str:
        return f"<UserLibrary(id={self.id}, user_id={self.user_id}, paper_id={self.paper_id})>"
