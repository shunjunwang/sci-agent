"""
M9 - 算法商城 API v9 路由

端点:
- GET  /algorithms                    算法列表（分类/搜索/分页）
- GET  /algorithms/{algorithm_id}     算法详情
- POST /algorithms/{algorithm_id}/execute  执行算法
- GET  /executions                    执行历史
- GET  /executions/{execution_id}     执行详情
"""
import math
import os
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.common import APIResponse
from app.services.algorithm_service import algorithm_service
from app.models.user import User

from app.api.v1.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/algorithms", response_model=APIResponse)
async def list_algorithms(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    category: Optional[str] = Query(None, description="分类筛选"),
    sort_by: str = Query("newest", description="排序: rating / usage / newest"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """算法列表 - 支持分类筛选、关键词搜索、分页排序。"""
    skip = (page - 1) * page_size
    items, total = await algorithm_service.search_algorithms(
        db, keyword=keyword, category=category, sort_by=sort_by,
        skip=skip, limit=page_size,
    )

    return APIResponse(
        code=0, message="success",
        data={
            "items": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "category": a.category,
                    "author_id": a.author_id,
                    "docker_image": a.docker_image,
                    "input_schema": a.input_schema,
                    "output_schema": a.output_schema,
                    "default_params": a.default_params,
                    "is_public": a.is_public,
                    "usage_count": a.usage_count,
                    "rating_avg": a.rating_avg,
                    "rating_count": a.rating_count,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
                for a in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
    )


@router.get("/algorithms/{algorithm_id}", response_model=APIResponse)
async def get_algorithm(
    algorithm_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """算法详情。"""
    a = await algorithm_service.get_algorithm(db, algorithm_id)
    if not a:
        raise NotFoundError(message="算法不存在")

    return APIResponse(
        code=0, message="success",
        data={
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "author_id": a.author_id,
            "docker_image": a.docker_image,
            "input_schema": a.input_schema,
            "output_schema": a.output_schema,
            "default_params": a.default_params,
            "is_public": a.is_public,
            "usage_count": a.usage_count,
            "rating_avg": a.rating_avg,
            "rating_count": a.rating_count,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        },
    )


@router.post("/algorithms/{algorithm_id}/execute", response_model=APIResponse)
async def execute_algorithm(
    algorithm_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """执行算法 - 在沙箱中运行算法模板。"""
    algorithm = await algorithm_service.get_algorithm(db, algorithm_id)
    if not algorithm:
        raise NotFoundError(message="算法不存在")

    execution = await algorithm_service.create_execution(
        db,
        algorithm=algorithm,
        user_id=str(user.id),
        params=algorithm.default_params or {},
        input_data={},
    )

    return APIResponse(
        code=0, message="算法已提交执行",
        data={
            "execution_id": execution.id,
            "algorithm_id": algorithm_id,
            "status": execution.status,
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
        },
    )


@router.get("/executions", response_model=APIResponse)
async def list_executions(
    user_id: Optional[str] = Query(None, description="按用户筛选"),
    algorithm_id: Optional[str] = Query(None, description="按算法筛选"),
    status: Optional[str] = Query(None, description="按状态筛选: queued / running / completed / failed / timeout"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行历史 - 分页查询算法执行记录。"""
    # P1-01: 强制限定为当前用户，防止越权查看他人记录
    if user_id and user_id != str(current_user.id):
        raise ForbiddenError(message="无权查看其他用户的执行记录")
    effective_user_id = user_id or str(current_user.id)

    skip = (page - 1) * page_size
    items, total = await algorithm_service.list_executions(
        db, user_id=effective_user_id, algorithm_id=algorithm_id, status=status,
        skip=skip, limit=page_size,
    )

    return APIResponse(
        code=0, message="success",
        data={
            "items": [
                {
                    "execution_id": e.id,
                    "algorithm_id": e.algorithm_id,
                    "user_id": e.user_id,
                    "sandbox_job_id": e.sandbox_job_id,
                    "params": e.params,
                    "input_data": e.input_data,
                    "output_data": e.output_data,
                    "status": e.status,
                    "execution_time": e.execution_time,
                    "cost": e.cost,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
    )


@router.get("/executions/{execution_id}", response_model=APIResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """执行详情 - 查询单条算法执行记录。"""
    e = await algorithm_service.get_execution(db, execution_id)
    if not e:
        raise NotFoundError(message="执行记录不存在")

    return APIResponse(
        code=0, message="success",
        data={
            "execution_id": e.id,
            "algorithm_id": e.algorithm_id,
            "user_id": e.user_id,
            "sandbox_job_id": e.sandbox_job_id,
            "params": e.params,
            "input_data": e.input_data,
            "output_data": e.output_data,
            "status": e.status,
            "execution_time": e.execution_time,
            "cost": e.cost,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        },
    )
