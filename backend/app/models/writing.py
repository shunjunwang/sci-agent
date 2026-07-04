"""
M5 - AI写作辅助 ORM 模型

提供 WritingDocument（写作文档）和 ContentTrace（内容溯源）两个模型。
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    pass


class WritingDocument(Base):
    """AI写作文档模型。

    Attributes:
        id: 文档唯一标识（UUID v4 主键）。
        user_id: 所属用户 ID（外键）。
        title: 文档标题。
        content: 文档正文（Markdown）。
        journal_name: 目标期刊名称。
        status: 文档状态（draft / published / archived）。
        ai_generated_ratio: AI 生成内容占比。
        created_at: 创建时间。
        updated_at: 最后更新时间。
    """

    __tablename__ = "writing_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID, primary_key=True, default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="未命名文档")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    journal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft",
    )
    ai_generated_ratio: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0.0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # 关系
    traces: Mapped[List["ContentTrace"]] = relationship(
        "ContentTrace", back_populates="document", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<WritingDocument(id={self.id}, title={self.title[:30]!r})>"


class ContentTrace(Base):
    """AI生成内容溯源模型。

    记录文档中 AI 生成的每个内容块及其引用的文献来源。

    Attributes:
        id: 溯源记录唯一标识（UUID v4 主键）。
        document_id: 所属文档 ID（外键）。
        block_index: 内容块在文档中的序号。
        ai_generated_text: AI 生成的内容文本。
        cited_paper_ids: 引用的论文 ID 列表（JSON）。
        prompt_used: 使用的提示词。
        model_used: 使用的 AI 模型名称。
        confidence: 置信度评分。
        created_at: 创建时间。
    """

    __tablename__ = "content_traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID, primary_key=True, default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID, ForeignKey("writing_documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    block_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    cited_paper_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # 关系
    document: Mapped["WritingDocument"] = relationship(
        "WritingDocument", back_populates="traces",
    )

    def __repr__(self) -> str:
        return f"<ContentTrace(id={self.id}, block={self.block_index}, doc={self.document_id})>"


class WritingPlan(Base):
    """P0-A: 写作计划模型。

    强制 Plan > Generate 流程，先大纲确认再逐节生成。

    Attributes:
        id: 计划唯一标识（自增主键）。
        user_id: 所属用户 ID（外键）。
        topic: 写作主题。
        title: 生成的标题。
        status: 计划状态（drafting / confirmed / generating / completed / cancelled）。
        sections_json: 各节信息 JSON。
            格式：[{id, title, summary, estimated_words, status, content, trace_data, key_references}]
        final_document_id: 完成后的最终文档 ID（外键）。
        style: 写作风格。
        language: 输出语言。
        created_at: 创建时间。
        updated_at: 最后更新时间。
    """

    __tablename__ = "writing_plans"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="drafting", server_default="drafting",
    )
    sections_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    final_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UniversalUUID, ForeignKey("writing_documents.id", ondelete="SET NULL"), nullable=True,
    )
    style: Mapped[str] = mapped_column(String(50), nullable=False, default="academic")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="zh")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<WritingPlan(id={self.id}, title={self.title[:30]!r}, status={self.status!r})>"
