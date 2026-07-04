"""
P0-I: 分享模式 — ShareLink ORM 模型
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.writing import WritingDocument


class ShareLink(Base):
    """受控分享链接模型。"""

    __tablename__ = "share_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("writing_documents.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_access_count: Mapped[int] = mapped_column(Integer, default=5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    allow_download: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_print: Mapped[bool] = mapped_column(Boolean, default=False)
    watermark_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    require_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    owner: Mapped["User"] = relationship("User", backref="share_links")
    document: Mapped["WritingDocument"] = relationship(
        "WritingDocument", backref="share_links"
    )

    def __repr__(self) -> str:
        return f"<ShareLink id={self.id} token={self.token[:8]}... doc={self.document_id}>"
