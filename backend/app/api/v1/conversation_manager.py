"""
P0-E: 对话搜索+管理 — API 端点

提供对话的置顶、重命名、软删除、恢复、永久删除和搜索功能。
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.conversation_manager import (
    ConversationListResult,
    ConversationSearchResult,
    PinRequest,
    RenameRequest,
)
from app.services.conversation_search_service import ConversationSearchService

router = APIRouter(prefix="/conversations", tags=["v1-对话管理"], dependencies=[Depends(get_current_user)])

# ── 辅助函数 ──────────────────────────────────────────


async def _get_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user: User,
    *,
    include_deleted: bool = False,
) -> Conversation:
    """获取对话，验证所有权。

    Args:
        db: 数据库会话。
        conversation_id: 对话 UUID。
        user: 当前用户。
        include_deleted: 是否包含已软删除的对话。

    Returns:
        Conversation ORM 实例。

    Raises:
        NotFoundError: 对话不存在。
        ForbiddenError: 不属于当前用户。
    """
    filters = [Conversation.id == conversation_id]
    if not include_deleted:
        filters.append(Conversation.deleted_at.is_(None))

    result = await db.execute(select(Conversation).where(*filters))
    conv = result.scalar_one_or_none()

    if conv is None:
        raise NotFoundError(message="对话不存在")

    if conv.user_id != user.id:
        raise ForbiddenError(message="无权操作此对话")

    return conv


# ── 重命名 ────────────────────────────────────────────


@router.patch("/{conversation_id}/rename", response_model=APIResponse[None])
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: RenameRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """重命名对话。

    PATCH /api/v1/conversations/{conversation_id}/rename
    """
    conv = await _get_conversation(db, conversation_id, user)

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv.id)
        .values(title=body.title, updated_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return APIResponse(code=200, message="重命名成功")


# ── 置顶/取消置顶 ─────────────────────────────────────


@router.patch("/{conversation_id}/pin", response_model=APIResponse[None])
async def pin_conversation(
    conversation_id: uuid.UUID,
    body: PinRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """置顶/取消置顶对话。

    PATCH /api/v1/conversations/{conversation_id}/pin
    """
    conv = await _get_conversation(db, conversation_id, user)

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv.id)
        .values(pinned=body.pinned, updated_at=datetime.now(timezone.utc))
    )
    await db.commit()

    msg = "已置顶" if body.pinned else "已取消置顶"
    return APIResponse(code=200, message=msg)


# ── 软删除 ────────────────────────────────────────────


@router.delete("/{conversation_id}", response_model=APIResponse[None])
async def soft_delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """软删除对话（移入回收站）。

    DELETE /api/v1/conversations/{conversation_id}
    """
    conv = await _get_conversation(db, conversation_id, user)

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv.id)
        .values(deleted_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return APIResponse(code=200, message="已移入回收站")


# ── 恢复 ──────────────────────────────────────────────


@router.post("/{conversation_id}/restore", response_model=APIResponse[None])
async def restore_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """从回收站恢复对话。

    POST /api/v1/conversations/{conversation_id}/restore
    """
    conv = await _get_conversation(db, conversation_id, user, include_deleted=True)

    if conv.deleted_at is None:
        return APIResponse(code=200, message="对话未被删除，无需恢复")

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv.id)
        .values(deleted_at=None, updated_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return APIResponse(code=200, message="已恢复")


# ── 回收站列表 ────────────────────────────────────────


@router.get("/trash", response_model=APIResponse[list[ConversationListResult]])
async def list_trash(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取回收站列表。

    GET /api/v1/conversations/trash
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user.id,
            Conversation.deleted_at.isnot(None),
        )
        .order_by(Conversation.deleted_at.desc())
    )
    convs = result.scalars().all()

    items = [
        ConversationListResult(
            id=str(c.id),
            title=c.title,
            pinned=c.pinned,
            deleted_at=c.deleted_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in convs
    ]

    return APIResponse(code=200, message="success", data=items)


# ── 永久删除 ──────────────────────────────────────────


@router.delete("/{conversation_id}/permanent", response_model=APIResponse[None])
async def permanent_delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """永久删除对话（不可恢复）。

    DELETE /api/v1/conversations/{conversation_id}/permanent
    """
    conv = await _get_conversation(db, conversation_id, user, include_deleted=True)

    if conv.deleted_at is None:
        return APIResponse(code=400, message="请先移入回收站再永久删除")

    await db.delete(conv)
    await db.commit()

    return APIResponse(code=200, message="已永久删除")


# ── 搜索 ──────────────────────────────────────────────


@router.get("/search", response_model=APIResponse[list[ConversationSearchResult]])
async def search_conversations(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    scope: str = Query(default="title", description="搜索范围：title / global"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量上限"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """搜索对话。

    GET /api/v1/conversations/search?q=关键词&scope=title
    GET /api/v1/conversations/search?q=关键词&scope=global
    """
    if scope == "global":
        convs = await ConversationSearchService.search_global(db, user.id, q, limit)
    else:
        convs = await ConversationSearchService.search_by_title(db, user.id, q, limit)

    items = [
        ConversationSearchResult(
            id=str(c.id),
            title=c.title,
            updated_at=c.updated_at,
            pinned=c.pinned,
        )
        for c in convs
    ]

    return APIResponse(code=200, message="success", data=items)
