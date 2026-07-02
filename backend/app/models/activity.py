"""
ActivityLog ORM 模型。

映射到 activity_logs 表，记录用户行为日志，支持防篡改哈希链。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, JSON, String, Text, Uuid, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.user import User


class LogAction(str, Enum):
    """用户行为类型枚举。

    Attributes:
        CREATE: 创建资源。
        UPDATE: 更新资源。
        DELETE: 删除资源。
        EXPORT: 导出数据。
        SHARE: 分享资源。
        LOGIN: 用户登录。
        SEARCH: 检索操作。
        PAYMENT: 支付操作。
    """

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    SHARE = "share"
    LOGIN = "login"
    SEARCH = "search"
    PAYMENT = "payment"


class ActivityLog(Base):
    """用户行为日志模型。

    记录用户在平台上的所有关键操作，支持防篡改哈希链审计。

    Attributes:
        id: 日志唯一标识（UUID v4，主键）。
        user_id: 操作用户 ID（外键）。
        action: 行为类型（枚举）。
        resource_type: 操作资源类型（如 "paper", "document"）。
        resource_id: 操作资源 ID。
        detail: 行为详情（JSON，记录操作前后变化）。
        ip_address: 客户端 IP 地址。
        user_agent: 客户端 User-Agent。
        created_at: 记录时间（UTC）。

    Note:
        防篡改哈希链字段（prev_hash, current_hash）由应用层维护，
        不在 ORM 模型中直接映射，由日志写入服务统一计算。
    """

    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[LogAction] = mapped_column(
        SAEnum(LogAction, name="log_action", create_type=False),
        nullable=False,
    )
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(),
        nullable=True,
    )
    detail: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="activity_logs",
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, action={self.action.value})>"
