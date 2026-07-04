"""
P0-G: 三层记忆系统 — Schema 定义
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── 用户画像 ──────────────────────────────────────────


class UserProfileUpdate(BaseModel):
    """用户画像更新请求。"""

    research_domains: Optional[List[str]] = Field(None, description="研究领域列表")
    preferred_journals: Optional[List[str]] = Field(None, description="偏好期刊列表")
    writing_style: Optional[str] = Field(None, description="写作风格：academic/strict / conversational")
    preferred_language: Optional[str] = Field(None, description="首选语言：zh / en")
    citation_format: Optional[str] = Field(None, description="引文格式：gbt7714 / apa / mla / ieee")
    institution: Optional[str] = Field(None, description="所属机构")
    role: Optional[str] = Field(None, description="角色：phd_student / professor / undergrad")


class UserProfileResponse(BaseModel):
    """用户画像响应。"""

    id: int
    user_id: str
    research_domains: List[str]
    preferred_journals: List[str]
    writing_style: Optional[str]
    preferred_language: str
    citation_format: str
    institution: Optional[str]
    role: Optional[str]
    updated_at: datetime


# ── 课题记忆 ──────────────────────────────────────────


class TopicCreate(BaseModel):
    """创建课题记忆请求。"""

    topic_name: str = Field(..., min_length=1, max_length=200, description="课题名称")
    workspace_id: Optional[int] = Field(None, description="关联协作空间 ID")
    conventions: Optional[dict] = Field(default_factory=dict, description="课题约定")


class TopicUpdate(BaseModel):
    """更新课题记忆请求。"""

    topic_name: Optional[str] = Field(None, description="课题名称")
    key_papers: Optional[List[dict]] = Field(None, description="核心论文列表")
    pitfalls: Optional[List[dict]] = Field(None, description="踩坑记录列表")
    conventions: Optional[dict] = Field(None, description="课题约定")
    experiment_templates: Optional[dict] = Field(None, description="实验模板")


class TopicResponse(BaseModel):
    """课题记忆响应。"""

    id: int
    user_id: str
    workspace_id: Optional[int]
    topic_name: str
    conventions: dict
    key_papers: list
    pitfalls: list
    experiment_templates: dict
    status: str
    created_at: datetime
    updated_at: datetime


# ── 会话上下文 ────────────────────────────────────────


class UserContext(BaseModel):
    """注入对话用的轻量用户上下文。"""

    research_domains: List[str] = Field(default_factory=list)
    preferred_journals: List[str] = Field(default_factory=list)
    citation_format: str = "gbt7714"
    writing_style: str = "academic/strict"
    active_topics: List[str] = Field(default_factory=list)


class RecentContext(BaseModel):
    """最近 N 天研学摘要。"""

    daily_summaries: List[str] = Field(default_factory=list)
    total_papers_read: int = 0
    total_search_queries: int = 0
    total_words_written: int = 0
    total_sandbox_runs: int = 0


class SessionContextResponse(BaseModel):
    """会话上下文响应。"""

    id: int
    user_id: str
    session_date: date
    daily_summary: Optional[str]
    search_queries: list
    papers_read: list
    writing_sessions: list
    sandbox_runs: list
    created_at: datetime
