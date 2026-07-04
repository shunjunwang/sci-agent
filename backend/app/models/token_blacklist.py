"""
Token 黑名单 ORM 模型。

映射到 token_blacklist 表，记录已撤销的 JWT Token，
实现登出/刷新后的 Token 失效机制。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID


class TokenBlacklist(Base):
    """Token 黑名单记录。

    Attributes:
        id: 主键 UUID。
        token_jti: JWT Token 的唯一标识 (JWT ID)，唯一索引。
        user_id: 关联的用户 ID（外键）。
        token_type: Token 类型（access 或 refresh）。
        expires_at: Token 原始过期时间。
        revoked: 是否被撤销。
        created_at: 记录创建时间。
    """

    __tablename__ = "token_blacklist"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    token_jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────
    user = relationship("User", backref="revoked_tokens")

    def __repr__(self) -> str:
        return (
            f"<TokenBlacklist(id={self.id}, jti={self.token_jti}, "
            f"type={self.token_type})>"
        )
