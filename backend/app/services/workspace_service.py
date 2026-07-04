"""
M7 - 四级协作空间 业务服务

交付物来源: task-pc2-m7
核心逻辑: Workspace CRUD + RBAC 权限控制 + 邀请流程
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace, WorkspaceMember, Invitation


class WorkspaceService:
    """协作空间业务服务"""

    ROLE_PERMISSIONS = {
        "super_admin": {
            "manage_workspace", "manage_members", "change_roles",
            "invite", "remove_members", "send_tasks", "view_tasks",
            "submit_tasks", "view_feed", "manage_quota",
        },
        "admin": {
            "invite", "remove_members", "send_tasks", "view_tasks",
            "submit_tasks", "view_feed",
        },
        "leader": {
            "invite", "view_tasks", "submit_tasks", "view_feed",
        },
        "member": {
            "view_tasks", "submit_tasks", "view_feed",
        },
        "viewer": {
            "view_tasks", "view_feed",
        },
    }

    ROLE_HIERARCHY = {
        "super_admin": 5, "admin": 4, "leader": 3, "member": 2, "viewer": 1,
    }

    WORKSPACE_ROLES = ["super_admin", "admin", "leader", "member", "viewer"]
    WORKSPACE_LEVELS = ["school", "college", "lab", "class", "friends"]
    INVITATION_EXPIRE_DAYS = 7

    @classmethod
    def has_permission(cls, role: str, action: str) -> bool:
        return action in cls.ROLE_PERMISSIONS.get(role, set())

    @classmethod
    def validate_role(cls, role: str) -> bool:
        return role in cls.WORKSPACE_ROLES

    @classmethod
    def validate_level(cls, level: str) -> bool:
        return level in cls.WORKSPACE_LEVELS

    @classmethod
    def can_assign_role(cls, assigner_role: str, target_role: str) -> bool:
        assigner_level = cls.ROLE_HIERARCHY.get(assigner_role, 0)
        target_level = cls.ROLE_HIERARCHY.get(target_role, 0)
        return assigner_level >= 3 and assigner_level > target_level

    @classmethod
    def generate_invitation_code(cls, workspace_id: int, inviter_id: str) -> str:
        raw = f"{workspace_id}:{inviter_id}:{uuid.uuid4()}:{datetime.now(timezone.utc).isoformat()}"
        return f"inv_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"

    @classmethod
    def get_invitation_expiry(cls) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=cls.INVITATION_EXPIRE_DAYS)

    # ── Workspace CRUD ────────────────────────────

    @staticmethod
    async def create_workspace(
        db: AsyncSession, owner_id: str, name: str, level: str,
        parent_id: Optional[int] = None, description: Optional[str] = None,
    ) -> Workspace:
        ws = Workspace(
            name=name, level=level, parent_id=parent_id,
            owner_id=owner_id, description=description,
        )
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        member = WorkspaceMember(
            workspace_id=ws.id, user_id=owner_id, role="super_admin"
        )
        db.add(member)
        await db.commit()
        return ws

    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: int) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_workspaces(
        db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[dict], int]:
        stmt = (
            select(Workspace, WorkspaceMember.role)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        rows = result.all()

        count_stmt = select(func.count()).where(WorkspaceMember.user_id == user_id)
        total = (await db.execute(count_stmt)).scalar() or 0

        items = []
        for ws, role in rows:
            cnt_stmt = select(func.count()).where(
                WorkspaceMember.workspace_id == ws.id
            )
            member_count = (await db.execute(cnt_stmt)).scalar() or 0
            items.append({
                "id": ws.id, "name": ws.name, "level": ws.level,
                "parent_id": ws.parent_id, "owner_id": ws.owner_id,
                "description": ws.description, "member_count": member_count,
                "my_role": role, "created_at": ws.created_at,
            })
        return items, total

    @staticmethod
    async def update_workspace(
        db: AsyncSession, workspace_id: int,
        name: Optional[str] = None, description: Optional[str] = None,
    ) -> Optional[Workspace]:
        ws = await WorkspaceService.get_workspace(db, workspace_id)
        if not ws:
            return None
        if name:
            ws.name = name  # type: ignore[assignment]
        if description is not None:
            ws.description = description  # type: ignore[assignment]
        ws.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        await db.commit()
        await db.refresh(ws)
        return ws

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: int) -> bool:
        """删除协作空间。P2-11: 显式清理关联的 members 和 invitations 后再删除 workspace。"""
        ws = await WorkspaceService.get_workspace(db, workspace_id)
        if not ws:
            return False

        # P2-11: 显式清理关联数据
        from sqlalchemy import delete as sa_delete

        await db.execute(
            sa_delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        await db.execute(
            sa_delete(Invitation).where(
                Invitation.workspace_id == workspace_id
            )
        )

        await db.delete(ws)
        await db.commit()
        return True

    # ── Member ────────────────────────────────────

    @staticmethod
    async def get_member(
        db: AsyncSession, workspace_id: int, user_id: str
    ) -> Optional[WorkspaceMember]:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_members(db: AsyncSession, workspace_id: int) -> List[dict]:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        members = result.scalars().all()
        return [
            {
                "user_id": m.user_id,
                "nickname": "",
                "role": m.role,
                "joined_at": m.joined_at,
            }
            for m in members
        ]

    @staticmethod
    async def update_member_role(
        db: AsyncSession, workspace_id: int, user_id: str, new_role: str,
    ) -> Optional[WorkspaceMember]:
        member = await WorkspaceService.get_member(db, workspace_id, user_id)
        if not member:
            return None
        member.role = new_role  # type: ignore[assignment]
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, workspace_id: int, user_id: str
    ) -> bool:
        member = await WorkspaceService.get_member(db, workspace_id, user_id)
        if not member:
            return False
        await db.delete(member)
        await db.commit()
        return True

    # ── Invitation ────────────────────────────────

    @staticmethod
    async def create_invitation(
        db: AsyncSession, workspace_id: int, inviter_id: str,
        invitee_email: Optional[str] = None, invitee_phone: Optional[str] = None,
        role: str = "member",
    ) -> Invitation:
        code = WorkspaceService.generate_invitation_code(workspace_id, inviter_id)
        inv = Invitation(
            invitation_code=code, workspace_id=workspace_id,
            inviter_id=inviter_id, invitee_email=invitee_email,
            invitee_phone=invitee_phone, role=role,
            expires_at=WorkspaceService.get_invitation_expiry(),
        )
        db.add(inv)
        await db.commit()
        await db.refresh(inv)
        return inv

    @staticmethod
    async def get_invitation_by_code(db: AsyncSession, code: str) -> Optional[Invitation]:
        stmt = select(Invitation).where(Invitation.invitation_code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def accept_invitation(
        db: AsyncSession, code: str, user_id: str
    ) -> Optional[Invitation]:
        inv = await WorkspaceService.get_invitation_by_code(db, code)
        if not inv or inv.status != "pending":
            return None
        expires_at = inv.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            inv.status = "expired"  # type: ignore[assignment]
            await db.commit()
            return None
        inv.status = "accepted"  # type: ignore[assignment]
        inv.responded_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        member = WorkspaceMember(
            workspace_id=inv.workspace_id, user_id=user_id, role=inv.role
        )
        db.add(member)
        await db.commit()
        await db.refresh(inv)
        return inv

    @staticmethod
    async def decline_invitation(db: AsyncSession, code: str) -> Optional[Invitation]:
        inv = await WorkspaceService.get_invitation_by_code(db, code)
        if not inv or inv.status != "pending":
            return None
        inv.status = "declined"  # type: ignore[assignment]
        inv.responded_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        await db.commit()
        await db.refresh(inv)
        return inv


workspace_service = WorkspaceService()
