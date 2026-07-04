"""
科研偏好配置 ORM 模型。

每个用户一行，存储引用格式、期刊偏好、关键词、语言等配置。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime, ForeignKey, Integer, JSON, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.user import User


class ResearchPreference(Base):
    """科研偏好配置 — 每个用户一行。

    Attributes:
        id: 主键。
        user_id: 关联用户 UUID（唯一）。
        default_citation_style: 默认引用格式（gbt7714 / apa / mla / bibtex / chicago / vancouver）。
        preferred_journals: JSON 数组，偏好投稿期刊列表。
        research_keywords: JSON 数组，研究关键词。
        writing_language: 写作语言（zh / en）。
        auto_save_interval: 自动保存间隔（秒），0 表示禁用。
        created_at: 创建时间。
        updated_at: 最后更新时间。
    """

    __tablename__ = "research_preferences"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    default_citation_style: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="gbt7714",
        server_default="gbt7714",
    )
    preferred_journals: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
    )
    research_keywords: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
    )
    writing_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="zh",
        server_default="zh",
    )
    auto_save_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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

    # ── 关系 ────────────────────────────
    user: Mapped["User"] = relationship("User", backref="research_preference")

    def __repr__(self) -> str:
        return f"<ResearchPreference(user_id={self.user_id}, style={self.default_citation_style})>"
