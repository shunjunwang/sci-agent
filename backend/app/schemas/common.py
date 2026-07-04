"""
统一 Schema 定义模块。

提供所有 API 使用的通用 Pydantic 模型：标准响应包装、分页参数等。
"""

from typing import Any, Generic, Optional, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应包装模型。

    Attributes:
        code: HTTP 状态码或业务状态码。
        message: 响应消息。
        data: 响应数据（泛型），成功时使用。
        detail: 错误详情，失败时使用。
        request_id: 请求追踪 ID。
    """

    code: int = Field(default=200, description="状态码")
    status: Optional[str] = Field(default=None, description="状态标识（如 ok）")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    detail: Optional[Any] = Field(default=None, description="错误详情")
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="请求追踪 ID",
    )

    # P2-01: 拒绝未声明的额外字段，防止 status="ok" 等被静默丢弃
    model_config = {"extra": "forbid"}


class PaginationParams(BaseModel):
    """分页请求参数。

    Attributes:
        page: 当前页码，从 1 开始。
        page_size: 每页条数，默认 20，最大 100。
    """

    page: int = Field(default=1, ge=1, description="页码（从 1 开始）")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="每页条数（1-100）",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型。

    Attributes:
        items: 当前页数据列表。
        total: 总记录数。
        page: 当前页码。
        page_size: 每页条数。
        pages: 总页数。
    """

    items: list[T] = Field(default_factory=list, description="当前页数据")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")
    pages: int = Field(default=0, description="总页数")


# P2-03: 统一构建分页响应，消除跨多个路由的重复代码
def build_paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """构建标准分页响应 dict。

    Args:
        items: 当前页数据列表。
        total: 总记录数。
        page: 当前页码。
        page_size: 每页条数。

    Returns:
        标准分页响应字典，可直接作为 APIResponse.data 使用。
    """
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
