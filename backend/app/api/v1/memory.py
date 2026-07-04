"""
P0-G: 三层记忆系统 — API 端点
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.memory import UserProfile, TopicMemory
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.memory import (
    UserProfileUpdate,
    UserProfileResponse,
    TopicCreate,
    TopicUpdate,
)
from app.services.memory_engine import memory_engine

router = APIRouter(prefix="/memory", tags=["记忆系统"], dependencies=[Depends(get_current_user)])


# ── 用户画像 ──────────────────────────────────────


@router.get("/context", response_model=APIResponse[dict])
async def get_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """获取当前用户轻量上下文（注入对话用）。"""
    ctx = await memory_engine.get_user_context(db, current_user.id)
    return APIResponse(code=200, message="success", data=ctx)


@router.post("/preferences", response_model=APIResponse[UserProfileResponse])
async def update_preferences(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfileResponse]:
    """更新用户画像。"""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)

    return APIResponse(
        code=200,
        message="success",
        data=UserProfileResponse(
            id=profile.id,
            user_id=str(profile.user_id),
            research_domains=profile.research_domains or [],
            preferred_journals=profile.preferred_journals or [],
            writing_style=profile.writing_style,
            preferred_language=profile.preferred_language,
            citation_format=profile.citation_format,
            institution=profile.institution,
            role=profile.role,
            updated_at=profile.updated_at,
        ),
    )


# ── 课题记忆 ──────────────────────────────────────


@router.get("/topics", response_model=APIResponse[list])
async def list_topics(
    status: str = Query(default=None, description="active / archived"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list]:
    """获取当前用户所有课题记忆。"""
    filters = [TopicMemory.user_id == current_user.id]
    if status:
        filters.append(TopicMemory.status == status)

    result = await db.execute(
        select(TopicMemory).where(*filters).order_by(TopicMemory.updated_at.desc())
    )
    topics = result.scalars().all()

    return APIResponse(
        code=200,
        message="success",
        data=[
            {
                "id": t.id,
                "user_id": str(t.user_id),
                "workspace_id": t.workspace_id,
                "topic_name": t.topic_name,
                "conventions": t.conventions,
                "key_papers": t.key_papers or [],
                "pitfalls": t.pitfalls or [],
                "experiment_templates": t.experiment_templates or {},
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in topics
        ],
    )


@router.post("/topics", response_model=APIResponse[dict], status_code=201)
async def create_topic(
    data: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """创建课题记忆。"""
    topic = await memory_engine.create_topic(
        db=db,
        user_id=current_user.id,
        topic_name=data.topic_name,
        workspace_id=data.workspace_id,
        conventions=data.conventions,
    )
    await db.commit()
    await db.refresh(topic)

    return APIResponse(
        code=201,
        message="课题创建成功",
        data={
            "id": topic.id,
            "user_id": str(topic.user_id),
            "workspace_id": topic.workspace_id,
            "topic_name": topic.topic_name,
            "conventions": topic.conventions,
            "key_papers": topic.key_papers or [],
            "pitfalls": topic.pitfalls or [],
            "experiment_templates": topic.experiment_templates or {},
            "status": topic.status,
            "created_at": topic.created_at.isoformat() if topic.created_at else None,
            "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
        },
    )


@router.patch("/topics/{topic_id}", response_model=APIResponse[dict])
async def update_topic(
    topic_id: int,
    data: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """更新课题记忆。"""
    result = await db.execute(
        select(TopicMemory).where(
            TopicMemory.id == topic_id,
            TopicMemory.user_id == current_user.id,
        )
    )
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="课题记忆不存在")
    if topic.status == "archived":
        raise HTTPException(status_code=400, detail="已归档的课题不可修改")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(topic, field, value)

    await db.flush()
    await db.refresh(topic)

    return APIResponse(
        code=200,
        message="课题更新成功",
        data={
            "id": topic.id,
            "user_id": str(topic.user_id),
            "topic_name": topic.topic_name,
            "conventions": topic.conventions,
            "key_papers": topic.key_papers or [],
            "pitfalls": topic.pitfalls or [],
            "experiment_templates": topic.experiment_templates or {},
            "status": topic.status,
            "created_at": topic.created_at.isoformat() if topic.created_at else None,
            "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
        },
    )


@router.post("/topics/{topic_id}/archive", response_model=APIResponse[dict])
async def archive_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """归档课题。"""
    result = await db.execute(
        select(TopicMemory).where(
            TopicMemory.id == topic_id,
            TopicMemory.user_id == current_user.id,
        )
    )
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="课题记忆不存在")

    topic.status = "archived"
    await db.flush()

    return APIResponse(code=200, message="课题已归档", data={"id": topic_id, "status": "archived"})


# ── 会话上下文 ──────────────────────────────────────


@router.get("/recent", response_model=APIResponse[dict])
async def get_recent_context(
    days: int = Query(default=7, ge=1, le=365, description="查询天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """获取最近 N 天研学摘要。"""
    ctx = await memory_engine.get_recent_context(db, current_user.id, days=days)
    return APIResponse(code=200, message="success", data=ctx)


@router.get("/search", response_model=APIResponse[list])
async def search_memory(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list]:
    """搜索记忆库（课题论文 + 会话摘要）。"""
    results = await memory_engine.search_memory(db, current_user.id, q)
    return APIResponse(code=200, message="success", data=results)
