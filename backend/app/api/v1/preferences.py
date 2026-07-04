"""
科研偏好配置 API — GET / PUT。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.preference import PreferenceResponse, PreferenceUpdateRequest
from app.services.preference_service import preference_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/preferences", response_model=APIResponse[PreferenceResponse])
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PreferenceResponse]:
    """获取当前用户的科研偏好配置。"""
    user_id = str(current_user.id)
    pref = await preference_service.get_preferences(db, user_id)
    return APIResponse(code=200, message="success", data=pref)


@router.put("/preferences", response_model=APIResponse[PreferenceResponse])
async def update_preferences(
    data: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PreferenceResponse]:
    """更新当前用户的科研偏好配置。"""
    user_id = str(current_user.id)
    pref = await preference_service.update_preferences(db, user_id, data)
    return APIResponse(code=200, message="success", data=pref)
