"""
# mypy: disable-error-code="no-untyped-def"
PC2 M2 文献检索 API
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.paper import SearchHistory
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.paper import SearchHistoryItem, SearchHistoryResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.get("/search", response_model=APIResponse)
async def search_papers(
    q: str = Query(..., description="搜索关键词", max_length=500),
    sources: Optional[str] = Query(None, description="数据源（keying, arxiv, pubmed, cnki，逗号分隔多个）", max_length=200),
    author: Optional[str] = Query(None, description="作者过滤", max_length=200),
    journal: Optional[str] = Query(None, description="期刊名过滤", max_length=200),
    doi: Optional[str] = Query(None, description="DOI 精确查询", max_length=200),
    year_from: Optional[int] = Query(None, description="起始年份", ge=1800, le=2100),
    year_to: Optional[int] = Query(None, description="结束年份", ge=1800, le=2100),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """文献搜索 - 支持多源聚合检索、高级过滤"""
    sources_list = None
    if sources:
        sources_list = [s.strip() for s in sources.split(",") if s.strip()]

    result = await SearchService.search(
        query=q,
        sources=sources_list,
        page=page,
        page_size=page_size,
        author=author,
        journal=journal,
        doi=doi,
        year_from=year_from,
        year_to=year_to,
        db=db,
    )

    return APIResponse(
        code=0,
        message=f"搜索 '{q}' 完成",
        data=result
    )


@router.get("/history", response_model=APIResponse)
async def get_search_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="按来源过滤（arxiv/pubmed/cnki/keying）"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的搜索历史，支持分页与按来源过滤"""
    base_query = select(SearchHistory).where(SearchHistory.user_id == current_user.id)
    count_query = select(sa_func.count(SearchHistory.id)).where(
        SearchHistory.user_id == current_user.id
    )

    if source:
        base_query = base_query.where(SearchHistory.source == source)
        count_query = count_query.where(SearchHistory.source == source)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    stmt = base_query.order_by(SearchHistory.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    items = [
        SearchHistoryItem(
            id=row.id,
            query=row.query,
            source=row.source,
            page=row.page,
            page_size=row.page_size,
            total_results=row.total_results,
            created_at=row.created_at.isoformat() if row.created_at else None,
        )
        for row in rows
    ]

    pages = math.ceil(total / limit) if total > 0 else 0

    response_data = SearchHistoryResponse(
        items=items,
        total=total,
        page=offset // limit + 1 if limit > 0 else 1,
        page_size=limit,
        pages=pages,
    )

    return APIResponse(
        code=0,
        message=f"搜索历史（共 {total} 条）",
        data=response_data.model_dump(),
    )


@router.get("/{paper_id}", response_model=APIResponse)
async def get_paper_detail(
    paper_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取文献详情"""
    detail = await SearchService.get_detail(paper_id)
    if not detail:
        raise NotFoundError(message=f"文献 {paper_id} 未找到")

    return APIResponse(
        code=0,
        message=f"文献 {paper_id} 详情",
        data=detail.model_dump()
    )


@router.get("/{paper_id}/pdf")
async def download_paper_pdf(
    paper_id: str,
    current_user: User = Depends(get_current_user),
):
    """下载文献 PDF - 重定向到原始 PDF 链接"""
    pdf_url = await SearchService.get_pdf_url(paper_id)
    if not pdf_url:
        raise NotFoundError(message=f"文献 {paper_id} 的 PDF 不可用")

    return RedirectResponse(url=pdf_url)
