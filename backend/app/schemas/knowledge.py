"""
知识库相关 Pydantic 模型 — 请求体 / 响应体 / 枚举。

所有输入/输出经过严格校验，与 APIResponse 包装层解耦。
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ── 枚举 ──────────────────────────────────────────


class ReadStatus(str, Enum):
    unread = "unread"
    reading = "reading"
    finished = "finished"


class CitationFormat(str, Enum):
    gbt7714 = "gbt7714"
    apa = "apa"
    mla = "mla"
    bibtex = "bibtex"
    chicago = "chicago"
    vancouver = "vancouver"


class SearchScope(str, Enum):
    title = "title"
    abstract = "abstract"
    notes = "notes"
    all = "all"


# ── 知识库文献 ────────────────────────────────────


class LibraryPaperCreate(BaseModel):
    """添加文献到知识库。"""
    paper_id: str = Field(..., description="文献标识符（如 arxiv:2401.12345、keying:abc123）")
    folder: Optional[str] = Field(None, max_length=500, description="目标文件夹路径")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    notes: Optional[str] = Field(None, description="初始笔记")


class LibraryPaperUpdate(BaseModel):
    """更新知识库条目。"""
    folder: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    is_favorited: Optional[bool] = None
    read_status: Optional[ReadStatus] = None
    notes: Optional[str] = None


class PaperMeta(BaseModel):
    """文献元数据（来自 papers 表）。"""
    paper_id: str
    title: str
    authors: list = []
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None

    class Config:
        from_attributes = True


class LibraryPaperOut(BaseModel):
    """知识库条目完整响应。"""
    id: int
    user_id: int
    paper: Optional[PaperMeta] = None
    folder: Optional[str] = None
    tags: List[str] = []
    is_favorited: bool = False
    read_status: ReadStatus = ReadStatus.unread
    notes: Optional[str] = None
    added_at: Optional[datetime] = None
    last_read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── 文件夹 ────────────────────────────────────────


class FolderCreate(BaseModel):
    """创建文件夹。"""
    path: str = Field(..., max_length=500, description="文件夹路径，如 机器学习/深度学习")


class FolderNode(BaseModel):
    """文件夹树节点。"""
    path: str
    count: int = 0
    children: List["FolderNode"] = []


FolderNode.model_rebuild()


# ── 批注 ──────────────────────────────────────────


class PositionData(BaseModel):
    """批注位置信息。"""
    page: Optional[int] = None
    paragraph: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None


class AnnotationCreate(BaseModel):
    """添加批注。"""
    library_id: int = Field(..., description="知识库条目 ID")
    highlighted_text: Optional[str] = Field(None, description="高亮文本片段")
    note: str = Field(..., description="批注笔记")
    position: Optional[PositionData] = None


class AnnotationOut(BaseModel):
    """批注响应。"""
    id: int
    library_id: int
    highlighted_text: Optional[str] = None
    note: Optional[str] = None
    position_data: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── 引用导出 ──────────────────────────────────────


class CitationExportRequest(BaseModel):
    """引用导出请求。"""
    library_ids: List[int] = Field(..., min_length=1, description="知识库条目 ID 列表")
    format: CitationFormat = Field(..., description="导出格式")


# ── 引用图谱 ──────────────────────────────────────


class GraphNode(BaseModel):
    id: str
    label: str
    group: str  # "center" | "reference" | "cited_by"


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # "cites" | "cited_by"


class CitationGraphOut(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


# ── 搜索 ──────────────────────────────────────────


class KnowledgeSearchParams(BaseModel):
    q: str = Field(..., min_length=1, description="搜索关键词")
    search_in: SearchScope = SearchScope.all
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class KnowledgeSearchResult(BaseModel):
    library_id: int
    paper_title: str
    match_in: str  # "title" | "abstract" | "notes"
    snippet: str
    relevance_score: float = 0.0
