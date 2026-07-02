"""
Workspace / WorkspaceMember ORM 模型。

映射到 workspaces 和 workspace_members 表，管理协作空间及成员关系。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, Text, Uuid, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.user import User


class WorkspaceRole(str, Enum):
    """协作空间角色枚举。

    Attributes:
        OWNER: 创建者，拥有全部权限。
        EDITOR: 编辑者，可添加文献、创建任务。
        VIEWER: 观察者，只读权限。
    """

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Workspace(Base):
    """协作空间模型。

    管理课题组的协作空间，支持多成员、多角色权限控制。

    Attributes:
        id: 空间唯一标识（UUID v4，主键）。
        name: 空间名称。
        description: 空间描述。
        owner_id: 创建者 ID（外键）。
        is_public: 是否公开可见。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
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
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
    )
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name!r})>"


class WorkspaceMember(Base):
    """协作空间成员模型。

    管理协作空间与用户之间的成员关系及角色。

    Attributes:
        id: 记录唯一标识（UUID v4，主键）。
        workspace_id: 协作空间 ID（外键）。
        user_id: 用户 ID（外键）。
        role: 成员角色（枚举）。
        joined_at: 加入时间（UTC）。

    Note:
        (workspace_id, user_id) 有唯一约束，同一用户在同一空间不可重复加入。
    """

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_ws_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        SAEnum(WorkspaceRole, name="workspace_role", create_type=False),
        nullable=False,
        default=WorkspaceRole.VIEWER,
        server_default="viewer",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── 关系 ─────────────────────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workspace_memberships",
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMember(id={self.id}, workspace_id={self.workspace_id}, role={self.role.value})>"
