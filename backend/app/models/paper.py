"""
Paper ORM 模型。

映射到 papers 表，存储文献元数据、摘要、embedding 向量等。
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.annotation import Annotation
    from app.models.library import UserLibrary
    from app.models.user import User


class PaperSource(str, Enum):
    """文献来源枚举。

    Attributes:
        OPENALEX: OpenAlex 开放学术数据。
        CNKI: 中国知网。
        WANFANG: 万方数据。
        CQVIP: 维普期刊。
        MANUAL_IMPORT: 手动导入。
        ZOTERO: Zotero 文献管理器。
        MENDELEY: Mendeley 文献管理器。
        SCHOLAR: Google Scholar。
    """

    OPENALEX = "openalex"
    CNKI = "cnki"
    WANFANG = "wanfang"
    CQVIP = "cqvip"
    MANUAL_IMPORT = "manual_import"
    ZOTERO = "zotero"
    MENDELEY = "mendeley"
    SCHOLAR = "scholar"


class Paper(Base):
    """文献模型。

    Attributes:
        id: 文献唯一标识（UUID v4，主键）。
        paper_uid: 文献展示唯一标识，格式 paper_{uuid前8位}，可由 display_uid 属性自动生成。
        openalex_id: OpenAlex 系统中的文献 ID。
        doi: 数字对象标识符（唯一）。
        title: 文献标题。
        abstract: 摘要全文。
        authors: 作者列表（JSON，如 [{"name": "...", "affiliation": "..."}]）。
        publication_date: 出版日期。
        journal: 期刊/会议名称。
        source_db: 数据来源（枚举）。
        language: 语言代码，默认 "en"。
        citation_count: 被引次数。
        keywords: 关键词数组。
        references_json: 参考文献列表（JSON）。
        raw_metadata: 扩展元数据（JSON，来源特定字段）。
        full_text_url: 全文链接。
        embedding: 1536 维语义向量（JSON，生产环境建议迁移 pgvector）。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    paper_uid: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="文献唯一标识，格式 paper_{uuid前8位}",
    )
    openalex_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    doi: Mapped[Optional[str]] = mapped_column(
        String(500),
        unique=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    abstract: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    authors: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    publication_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    journal: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    source_db: Mapped[PaperSource] = mapped_column(
        SAEnum(PaperSource, name="paper_source", create_type=False),
        nullable=False,
        default=PaperSource.OPENALEX,
        server_default="openalex",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        server_default="en",
    )
    citation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )
    keywords: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
    )
    references_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    raw_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    full_text_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # TODO: 生产环境建议迁移到 pgvector 以获得更好的向量检索性能
    embedding: Mapped[Optional[list]] = mapped_column(
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

    # ── PC2 M2 新增字段 ─────────────────────────────────────────────────────
    search_source: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )  # 检索来源：keying / arxiv / pubmed / cnki
    full_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # 全文内容
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0,
    )  # 相关性评分
    volume: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 卷
    issue: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 期
    pages: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 页码
    citations_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )  # 引用本文的文献列表（JSON）

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user_library: Mapped[List["UserLibrary"]] = relationship(
        "UserLibrary",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    annotations: Mapped[List["Annotation"]] = relationship(
        "Annotation",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    @property
    def display_uid(self) -> str:
        """展示用唯一标识，从 UUID 自动生成（格式 paper_{hex前8位}）。"""
        return f"paper_{self.id.hex[:8]}"

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, title={self.title[:40]!r})>"


class SearchHistory(Base):
    """搜索历史模型 (PC2 M2)。

    记录用户的文献检索查询历史。
    """

    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    page: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )
    page_size: Mapped[int] = mapped_column(
        Integer,
        default=20,
    )
    total_results: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped[Optional["User"]] = relationship("User", backref="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory(id={self.id}, query={self.query[:40]!r})>"
