"""
PC2 M2 通用数据模型
"""

from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    """API 统一响应格式"""
    status: str  # "ok" | "error"
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    error_details: Optional[Any] = None


class Pagination(BaseModel):
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: int


class ErrorResponse(BaseModel):
    """错误响应"""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Any] = None