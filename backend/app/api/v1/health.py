"""
健康检查 API 路由。

提供服务状态和数据库连接状态的端点。
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.core.database import check_db_connection
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[dict])
async def health_check() -> APIResponse[dict]:
    """服务健康检查。

    返回服务当前版本和服务器时间戳。

    Returns:
        APIResponse: 包含状态、版本和时间戳的响应。
    """
    return APIResponse(
        code=200,
        message="success",
        data={
            "status": "ok",
            "version": settings.APP_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/health/db", response_model=APIResponse[dict])
async def health_db() -> APIResponse[dict]:
    """数据库连接健康检查。

    Returns:
        APIResponse: 包含数据库连接状态。
    """
    db_ok = await check_db_connection()
    return APIResponse(
        code=200 if db_ok else 503,
        message="success" if db_ok else "database unavailable",
        data={
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
