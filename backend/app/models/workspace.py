"""
M7 统一 Workspace ORM 模型 — 五级层级 + 完整权限体系

P1-24: 将 workspace_m7.py 的内容统一到本文件，WorkspaceM7 → Workspace，
WorkspaceMemberM7 → WorkspaceMember，InvitationM7 → Invitation。
旧版简单模型（UUID + 3角色）已重命名为 Legacy 变体，仅保留向后兼容。
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID


if TYPE_CHECKING:
    from app.models.user import User


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# M7 统一模型（主力）
# =============================================================================

class Workspace(Base):
    """协作空间 (M7 版本：五级层级 + int PK)

    映射到 workspaces_m7 表。
    """

    __tablename__ = "workspaces_m7"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    level = Column(
        String(20),
        nullable=False,
        comment="school / college / lab / class / friends",
    )
    parent_id = Column(Integer, ForeignKey("workspaces_m7.id"), nullable=True)
    owner_id = Column(String(36), nullable=False, index=True, comment="UUID 字符串，关联 users.id")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now_utc, nullable=False)
    updated_at = Column(DateTime, default=_now_utc, onupdate=_now_utc)

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name='{self.name}', level='{self.level}')>"


class WorkspaceMember(Base):
    """协作空间成员 (M7 版本：五级角色)

    映射到 workspace_members_m7 表。
    """

    __tablename__ = "workspace_members_m7"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member_m7"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces_m7.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True, comment="UUID 字符串")
    role = Column(
        String(20),
        nullable=False,
        default="member",
        comment="super_admin / admin / leader / member / viewer",
    )
    joined_at = Column(DateTime, default=_now_utc, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkspaceMember(ws={self.workspace_id}, user={self.user_id}, role='{self.role}')>"


class Invitation(Base):
    """邀请 (M7 版本)

    映射到 invitations_m7 表。
    """

    __tablename__ = "invitations_m7"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invitation_code = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces_m7.id"), nullable=False, index=True)
    inviter_id = Column(String(36), nullable=False, comment="UUID 字符串")
    invitee_email = Column(String(255), nullable=True)
    invitee_phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="member")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending / accepted / declined / expired",
    )
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_now_utc, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Invitation(code='{self.invitation_code}', status='{self.status}')>"


# =============================================================================
# 旧版模型（已废弃，仅向后兼容 user.py 中的 relationship）
# =============================================================================

# DEPRECATED: 以下 Workspace / WorkspaceMember / WorkspaceRole 为旧版简单模型，
# 映射到 workspaces / workspace_members 表，仅供 user.py 的向后兼容 relationship 使用。
# 新代码应使用上方的 M7 统一模型。

class WorkspaceRole(str, Enum):
    """协作空间角色枚举 (DEPRECATED: 旧版 3 角色)"""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class WorkspaceLegacy(Base):
    """协作空间模型 (DEPRECATED: 旧版 UUID + 3角色)

    映射到 workspaces 表，仅供向后兼容。
    """

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
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
        UniversalUUID,
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

    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
    )
    members: Mapped[List["WorkspaceMemberLegacy"]] = relationship(
        "WorkspaceMemberLegacy",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<WorkspaceLegacy(id={self.id}, name={self.name!r})>"


class WorkspaceMemberLegacy(Base):
    """协作空间成员模型 (DEPRECATED: 旧版 UUID + 3角色)

    映射到 workspace_members 表，仅供向后兼容。
    """

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_ws_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        String(20),
        nullable=False,
        default=WorkspaceRole.VIEWER,
        server_default="viewer",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    workspace: Mapped["WorkspaceLegacy"] = relationship(
        "WorkspaceLegacy",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workspace_memberships",
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMemberLegacy(id={self.id}, ws={self.workspace_id}, role={self.role.value})>"
