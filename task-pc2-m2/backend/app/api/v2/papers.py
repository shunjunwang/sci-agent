"""
PC2 M2 文献检索 API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.schemas.common import APIResponse
from app.schemas.paper import PaperSearchResult, PaperDetail

router = APIRouter()


@router.get("/search", response_model=APIResponse)
async def search_papers(
    q: str = Query(..., description="搜索关键词"),
    source: Optional[str] = Query(None, description="数据源（keying, arxiv, pubmed, cnki）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """文献搜索"""
    # TODO: 实现科应 API 调用
    # TODO: 实现多源聚合
    return APIResponse(
        status="ok",
        message=f"搜索 '{q}' 的结果",
        data={
            "query": q,
            "source": source or "all",
            "page": page,
            "page_size": page_size,
            "total": 0,
            "results": []
        }
    )


@router.get("/{paper_id}", response_model=APIResponse)
async def get_paper_detail(paper_id: str):
    """获取文献详情"""
    # TODO: 根据 paper_id 获取文献详情
    return APIResponse(
        status="ok",
        message=f"文献 {paper_id} 的详情",
        data={
            "id": paper_id,
            "title": "示例文献标题",
            "authors": ["作者1", "作者2"],
            "abstract": "这是文献摘要...",
            "source": "keying",
            "published_at": "2024-01-01",
            "doi": "10.1234/example"
        }
    )


@router.get("/{paper_id}/pdf")
async def download_paper_pdf(paper_id: str):
    """下载文献 PDF"""
    # TODO: 实现 PDF 下载代理
    raise HTTPException(status_code=501, detail="PDF 下载功能待实现")