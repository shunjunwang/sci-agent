"""
P0-E: 对话搜索+管理 — Schema 定义
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RenameRequest(BaseModel):
    """重命名对话的请求体。"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="新标题（1-200 字符）",
    )


class PinRequest(BaseModel):
    """置顶/取消置顶的请求体。"""

    pinned: bool = Field(..., description="是否置顶")


class ConversationSearchResult(BaseModel):
    """对话搜索结果。"""

    id: str = Field(..., description="对话 UUID")
    title: Optional[str] = Field(None, description="对话标题")
    updated_at: datetime = Field(..., description="最后更新时间")
    pinned: bool = Field(False, description="是否置顶")


class ConversationListResult(BaseModel):
    """对话列表项（用于回收站等）。"""

    id: str = Field(..., description="对话 UUID")
    title: Optional[str] = Field(None, description="对话标题")
    pinned: bool = Field(False, description="是否置顶")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")


class SearchRequest(BaseModel):
    """搜索请求查询参数的结构化表示。"""

    q: str = Field(..., min_length=1, description="搜索关键词")
    scope: str = Field(default="title", description="搜索范围：title / global")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量上限")
