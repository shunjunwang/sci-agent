"""
M7 - 四级协作空间 API v1 路由

交付物来源: task-pc2-m7
端点: Workspace CRUD + 成员管理 + 邀请流程 + 权限检查
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.schemas.workspace_m7 import (
    WorkspaceCreateRequest, WorkspaceUpdateRequest,
    MemberRoleUpdateRequest, InvitationCreateRequest, InvitationAcceptRequest,
)
from app.schemas.common import APIResponse, build_paginated_response
from app.services.workspace_service import workspace_service
from app.models.user import User

router = APIRouter()


# ==================== Workspace CRUD ====================

@router.post("/workspaces", response_model=APIResponse)
async def create_workspace(
    request: WorkspaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    if not workspace_service.validate_level(request.level):
        raise HTTPException(status_code=400, detail=f"无效的空间层级: {request.level}")

    ws = await workspace_service.create_workspace(
        db, owner_id=user_id, name=request.name,
        level=request.level, parent_id=request.parent_id,
        description=request.description,
    )
    return APIResponse(
        code=0, message="协作空间已创建",
        data={
            "id": ws.id, "name": ws.name, "level": ws.level,
            "owner_id": ws.owner_id, "description": ws.description,
        },
    )


@router.get("/workspaces", response_model=APIResponse)
async def list_workspaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    items, total = await workspace_service.list_workspaces(db, user_id, page, page_size)
    return APIResponse(
        code=0, message="success",
        data=build_paginated_response(items=items, total=total, page=page, page_size=page_size),
    )


@router.get("/workspaces/{workspace_id}", response_model=APIResponse)
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    ws = await workspace_service.get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="协作空间不存在")
    member = await workspace_service.get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此空间")
    return APIResponse(
        code=0, message="success",
        data={
            "id": ws.id, "name": ws.name, "level": ws.level,
            "parent_id": ws.parent_id, "owner_id": ws.owner_id,
            "description": ws.description, "created_at": ws.created_at,
        },
    )


@router.put("/workspaces/{workspace_id}", response_model=APIResponse)
async def update_workspace(
    workspace_id: int,
    request: WorkspaceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    member = await workspace_service.get_member(db, workspace_id, user_id)
    if not member or not workspace_service.has_permission(member.role, "manage_workspace"):
        raise HTTPException(status_code=403, detail="无权限更新此空间")

    ws = await workspace_service.update_workspace(
        db, workspace_id, name=request.name, description=request.description,
    )
    if not ws:
        raise HTTPException(status_code=404, detail="协作空间不存在")
    return APIResponse(code=0, message="空间信息已更新", data={"id": ws.id, "name": ws.name})


@router.delete("/workspaces/{workspace_id}", response_model=APIResponse)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    member = await workspace_service.get_member(db, workspace_id, user_id)
    if not member or member.role != "super_admin":
        raise HTTPException(status_code=403, detail="仅 super_admin 可删除空间")
    ok = await workspace_service.delete_workspace(db, workspace_id)
    if not ok:
        raise HTTPException(status_code=404, detail="协作空间不存在")
    return APIResponse(code=0, message="协作空间已删除", data=None)


# ==================== 成员管理 ====================

@router.get("/workspaces/{workspace_id}/members", response_model=APIResponse)
async def list_members(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    member = await workspace_service.get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此空间")
    members = await workspace_service.list_members(db, workspace_id)
    return APIResponse(code=0, message="success", data={"members": members})


@router.put("/workspaces/{workspace_id}/members/{target_user_id}", response_model=APIResponse)
async def update_member_role(
    workspace_id: int,
    target_user_id: str,
    request: MemberRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    if not workspace_service.validate_role(request.role):
        raise HTTPException(status_code=400, detail=f"无效的角色: {request.role}")

    me = await workspace_service.get_member(db, workspace_id, user_id)
    if not me or not workspace_service.has_permission(me.role, "change_roles"):
        raise HTTPException(status_code=403, detail="无权限修改角色")
    if not workspace_service.can_assign_role(me.role, request.role):
        raise HTTPException(status_code=403, detail="无法分配该角色")

    target = await workspace_service.update_member_role(
        db, workspace_id, target_user_id, request.role,
    )
    if not target:
        raise HTTPException(status_code=404, detail="成员不存在")
    return APIResponse(
        code=0, message="角色已更新",
        data={"user_id": target_user_id, "role": request.role},
    )


@router.delete("/workspaces/{workspace_id}/members/{target_user_id}", response_model=APIResponse)
async def remove_member(
    workspace_id: int,
    target_user_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    me = await workspace_service.get_member(db, workspace_id, user_id)
    if not me or not workspace_service.has_permission(me.role, "remove_members"):
        raise HTTPException(status_code=403, detail="无权限移除成员")
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="不能移除自己")

    ok = await workspace_service.remove_member(db, workspace_id, target_user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="成员不存在")
    return APIResponse(code=0, message="成员已移除", data=None)


# ==================== 邀请 ====================

@router.post("/workspaces/{workspace_id}/invitations", response_model=APIResponse)
async def create_invitation(
    workspace_id: int,
    request: InvitationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    me = await workspace_service.get_member(db, workspace_id, user_id)
    if not me or not workspace_service.has_permission(me.role, "invite"):
        raise HTTPException(status_code=403, detail="无权限发送邀请")
    if request.role and not workspace_service.validate_role(request.role):
        raise HTTPException(status_code=400, detail=f"无效的角色: {request.role}")

    inv = await workspace_service.create_invitation(
        db, workspace_id, user_id,
        invitee_email=request.invitee_email,
        invitee_phone=request.invitee_phone,
        role=request.role or "member",
    )
    return APIResponse(
        code=0, message="邀请已生成",
        data={
            "invitation_code": inv.invitation_code,
            "workspace_id": inv.workspace_id,
            "role": inv.role,
            "expires_at": inv.expires_at.isoformat(),
        },
    )


@router.post("/workspaces/invitations/accept", response_model=APIResponse)
async def accept_invitation(
    request: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    inv = await workspace_service.accept_invitation(db, request.invitation_code, user_id)
    if not inv:
        raise HTTPException(status_code=400, detail="邀请无效或已过期")
    return APIResponse(code=0, message="已加入协作空间", data={"workspace_id": inv.workspace_id})


@router.post("/workspaces/invitations/decline", response_model=APIResponse)
async def decline_invitation(
    request: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    inv = await workspace_service.decline_invitation(db, request.invitation_code)
    if not inv:
        raise HTTPException(status_code=400, detail="邀请无效")
    return APIResponse(code=0, message="已拒绝邀请", data=None)


# ==================== 权限检查 ====================

@router.get("/workspaces/{workspace_id}/permissions", response_model=APIResponse)
async def get_permissions(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    member = await workspace_service.get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=403, detail="不属于此空间")
    role = member.role
    return APIResponse(
        code=0, message="success",
        data={
            "role": role,
            "permissions": list(workspace_service.ROLE_PERMISSIONS.get(role, set())),
        },
    )
