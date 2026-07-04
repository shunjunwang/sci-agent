"""
M8 - 防篡改日志 API v1 路由
# mypy: disable-error-code="no-untyped-def"

交付物来源: task-pc1-m8
端点: GET /admin/activity-logs, GET /admin/activity-logs/verify, GET /admin/activity-logs/statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.schemas.common import APIResponse, build_paginated_response
from app.services.audit_service import audit_service
from app.models.user import User


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/admin/activity-logs", response_model=APIResponse)
async def query_activity_logs(
    user_id: str = Query(None),
    action_type: str = Query(None),
    date_from: str = Query(None, description="起始日期 ISO 8601"),
    date_to: str = Query(None, description="截止日期 ISO 8601"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    if action_type and not audit_service.validate_action_type(action_type):
        raise HTTPException(
            status_code=400,
            detail=f"无效的行为类型: {action_type}，有效值: {', '.join(audit_service.ACTION_TYPES)}",
        )

    items, total = await audit_service.query_logs(
        db, user_id=user_id, action_type=action_type,
        date_from=date_from, date_to=date_to,
        page=page, page_size=page_size,
    )

    return APIResponse(
        code=0, message="success",
        data=build_paginated_response(
            items=[
                {
                    "log_id": item.id,
                    "user_id": item.user_id,
                    "action_type": item.action_type,
                    "action_detail": item.action_detail,
                    "prev_hash": item.prev_hash,
                    "current_hash": item.current_hash,
                    "ip_address": item.ip_address,
                    "device_fingerprint": item.device_fingerprint,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ],
            total=total, page=page, page_size=page_size,
        ),
    )


@router.get("/admin/activity-logs/verify", response_model=APIResponse)
async def verify_integrity(
    user_id: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await audit_service.verify_logs(
        db, user_id=user_id, date_from=date_from, date_to=date_to,
    )
    return APIResponse(code=0, message="success", data=result)


@router.get("/admin/activity-logs/statistics", response_model=APIResponse)
async def activity_statistics(
    workspace_id: int = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    group_by: str = Query("date", description="聚合维度: user / action_type / date"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    if group_by not in ("user", "action_type", "date"):
        raise HTTPException(status_code=400, detail=f"无效的聚合维度: {group_by}")

    result = await audit_service.get_statistics(
        db, date_from=date_from, date_to=date_to, group_by=group_by,
    )
    return APIResponse(code=0, message="success", data=result)
