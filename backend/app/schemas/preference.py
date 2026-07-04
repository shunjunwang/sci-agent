"""
科研偏好配置 Schema — 请求/响应模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PreferenceResponse(BaseModel):
    """偏好配置响应。"""

    user_id: str
    default_citation_style: str = "gbt7714"
    preferred_journals: Optional[list[str]] = None
    research_keywords: Optional[list[str]] = None
    writing_language: str = "zh"
    auto_save_interval: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    """偏好配置更新请求 — 所有字段可选。"""

    default_citation_style: Optional[str] = Field(
        default=None,
        description="默认引用格式：gbt7714 / apa / mla / bibtex / chicago / vancouver",
    )
    preferred_journals: Optional[list[str]] = Field(
        default=None,
        description="偏好投稿期刊列表",
    )
    research_keywords: Optional[list[str]] = Field(
        default=None,
        description="研究关键词列表",
    )
    writing_language: Optional[str] = Field(
        default=None,
        description="写作语言：zh / en",
    )
    auto_save_interval: Optional[int] = Field(
        default=None,
        ge=0,
        description="自动保存间隔（秒），0 表示禁用",
    )
