"""
Document ORM 模型。

映射到 documents 表，管理用户写作文档，支持层级结构和语义向量检索。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID


if TYPE_CHECKING:
    from app.models.user import User


class Document(Base):
    """用户文档模型。

    管理用户创建的笔记、草稿、论文等文档，支持 Markdown 格式、
    层级结构（parent_id 自引用）、语义向量嵌入和版本控制。

    Attributes:
        id: 文档唯一标识（UUID v4，主键）。
        user_id: 所属用户 ID（外键）。
        title: 文档标题。
        content: 文档正文（Markdown）。
        doc_type: 文档类型（note / draft / paper / report）。
        format: 内容格式，默认 "markdown"。
        tags: 标签数组。
        is_archived: 是否已归档。
        parent_id: 父文档 ID（自引用外键，用于层级目录）。
        version: 版本号，默认 1。
        embedding: 1536 维语义向量（JSON）。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "documents"

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
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    doc_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="note",
        server_default="note",
    )
    format: Mapped[str] = mapped_column(
        String(20),
        default="markdown",
        server_default="markdown",
    )
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UniversalUUID,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    embedding: Mapped[Optional[dict]] = mapped_column(
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
        back_populates="documents",
    )
    children: Mapped[List["Document"]] = relationship(
        "Document",
        backref="parent",
        remote_side="[Document.id]",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title[:40]!r})>"
