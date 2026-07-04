"""
PC2 M2 健康检查 API
"""

from fastapi import APIRouter
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse)
async def health_check():
    """健康检查端点"""
    return APIResponse(
        status="ok",
        message="PC2 M2 文献检索服务运行正常",
        data={
            "service": "paper-search",
            "version": "0.2.0",
            "status": "healthy"
        }
    )
