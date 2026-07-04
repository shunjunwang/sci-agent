"""
P0-G: 三层记忆系统 — ORM 模型

UserProfile:  用户画像层（永久保留，跨项目）
TopicMemory:  课题记忆层（课题存续期内有效）
SessionContext: 会话上下文层（最近 30-90 天有效）
"""

import uuid as _uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base):
    """用户画像层 — 永久保留，跨项目。

    存储用户的研究领域、偏好期刊、写作风格等稳定特征。
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    research_domains: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    preferred_journals: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    writing_style: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    preferred_language: Mapped[str] = mapped_column(
        String(20),
        default="zh",
        server_default="zh",
    )
    citation_format: Mapped[str] = mapped_column(
        String(20),
        default="gbt7714",
        server_default="gbt7714",
    )
    institution: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", backref="user_profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"


class TopicMemory(Base):
    """课题记忆层 — 课题存续期内有效。

    存储课题约定、核心论文、踩坑记录、实验模板等。
    """

    __tablename__ = "topic_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    topic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    conventions: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        server_default="{}",
    )
    key_papers: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    pitfalls: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    experiment_templates: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        server_default="{}",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        server_default="active",
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

    def __repr__(self) -> str:
        return f"<TopicMemory(id={self.id}, topic_name={self.topic_name!r})>"


class SessionContext(Base):
    """会话上下文层 — 最近 30-90 天有效。

    按天聚合研学活动摘要，定时归档过期数据。
    """

    __tablename__ = "session_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    search_queries: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    papers_read: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    writing_sessions: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    sandbox_runs: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SessionContext(user_id={self.user_id}, date={self.session_date})>"
