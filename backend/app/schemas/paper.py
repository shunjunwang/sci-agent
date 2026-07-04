"""
PC2 M2 文献数据模型
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class PaperSearchResult(BaseModel):
    """文献搜索结果"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    source: str  # keying, arxiv, pubmed, cnki
    published_at: Optional[date] = None
    doi: Optional[str] = None
    citation_count: Optional[int] = None
    relevance_score: float = 0.0
    keywords: List[str] = []
    journal: Optional[str] = None


class PaperDetail(PaperSearchResult):
    """文献详情"""
    full_text: Optional[str] = None
    keywords: List[str] = []
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    pdf_url: Optional[str] = None
    references: List[str] = []
    citations: List[str] = []


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    sources: List[str] = ["keying", "arxiv", "pubmed"]
    filters: Optional[dict] = None
    page: int = 1
    page_size: int = 20


class SearchHistoryItem(BaseModel):
    """搜索历史条目"""
    id: int
    query: str
    source: Optional[str] = None
    page: int = 1
    page_size: int = 20
    total_results: int = 0
    created_at: Optional[str] = None


class SearchHistoryResponse(BaseModel):
    """搜索历史分页响应"""
    items: List[SearchHistoryItem]
    total: int
    page: int
    page_size: int
    pages: int
