"""
SandboxSession ORM 模型。

映射到 sandbox_sessions 表，管理 Docker 仿真沙箱会话生命周期。
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


class SandboxStatus(str, Enum):
    """沙箱会话状态枚举。

    Attributes:
        RUNNING: 运行中。
        STOPPED: 已停止。
        ERROR: 异常状态。
        COMPLETED: 已完成。
    """

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


class SandboxSession(Base):
    """沙箱会话模型。

    记录每个 Docker 沙箱会话的配置、状态和生命周期。

    Attributes:
        id: 会话唯一标识（UUID v4，主键）。
        user_id: 所属用户 ID（外键）。
        name: 会话名称。
        description: 会话描述。
        container_id: Docker 容器 ID。
        status: 会话状态（枚举）。
        config: 沙箱配置（JSON，如镜像、CPU/内存限制等）。
        started_at: 启动时间（UTC）。
        stopped_at: 停止时间（UTC）。
    """

    __tablename__ = "sandbox_sessions"

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
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    container_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[SandboxStatus] = mapped_column(
        SAEnum(SandboxStatus, name="sandbox_status", create_type=False),
        nullable=False,
        default=SandboxStatus.RUNNING,
        server_default="running",
    )
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    stopped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sandbox_sessions",
    )

    def __repr__(self) -> str:
        return f"<SandboxSession(id={self.id}, name={self.name!r}, status={self.status.value})>"
