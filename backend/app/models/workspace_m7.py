# =============================================================================
# DEPRECATED — M7 模型类已统一迁移到 workspace.py（P1-24）
#
# 原 WorkspaceM7  → workspace.Workspace
# 原 WorkspaceMemberM7 → workspace.WorkspaceMember
# 原 InvitationM7  → workspace.Invitation
#
# 本文件仅保留作为参考，请勿在新代码中引用。
# =============================================================================
"""
M7 - 四级协作空间 ORM 模型 [DEPRECATED]

交付物来源: task-pc2-m7
注意: 本文件内容已统一到 models/workspace.py，类名已更名。
      新代码请从 app.models.workspace 导入 Workspace / WorkspaceMember / Invitation。
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint,
)

from app.core.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceM7(Base):
    """协作空间 (M7 版本：五级层级 + int PK) [DEPRECATED: 请使用 workspace.Workspace]"""

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
        return f"<WorkspaceM7(id={self.id}, name='{self.name}', level='{self.level}')>"


class WorkspaceMemberM7(Base):
    """协作空间成员 (M7 版本：五级角色) [DEPRECATED: 请使用 workspace.WorkspaceMember]"""

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
        return f"<WorkspaceMemberM7(ws={self.workspace_id}, user={self.user_id}, role='{self.role}')>"


class InvitationM7(Base):
    """邀请 (M7 版本) [DEPRECATED: 请使用 workspace.Invitation]"""

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
        return f"<InvitationM7(code='{self.invitation_code}', status='{self.status}')>"
