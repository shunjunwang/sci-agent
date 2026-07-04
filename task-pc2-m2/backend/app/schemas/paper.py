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


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    sources: List[str]
    page: int
    page_size: int
    total: int
    results: List[PaperSearchResult]