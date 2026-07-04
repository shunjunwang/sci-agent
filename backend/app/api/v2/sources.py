"""
PC2 M2 数据源 API
"""

from fastapi import APIRouter
from app.schemas.common import APIResponse
from app.services.search_service import SearchService

router = APIRouter()
# 注意：此端点无需鉴权。list_sources 仅返回静态数据源名称列表，不含用户信息或敏感配置。


@router.get("/sources", response_model=APIResponse)
async def list_sources():
    """获取可用数据源列表"""
    sources = SearchService.get_available_sources()
    return APIResponse(
        status="ok",
        message="可用数据源列表",
        data={"sources": sources}
    )
