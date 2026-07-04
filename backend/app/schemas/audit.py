"""
M8 - 防篡改日志 Schemas

交付物来源: task-pc1-m8
"""
from pydantic import BaseModel, Field
from typing import Optional


class AuditLogQueryParams(BaseModel):
    user_id: Optional[str] = None
    action_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class VerifyQueryParams(BaseModel):
    user_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class StatisticsQueryParams(BaseModel):
    workspace_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    group_by: str = "date"
