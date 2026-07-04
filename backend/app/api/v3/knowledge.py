"""
知识库 API 路由 — 全部端点（已适配主项目 ORM）。

路由前缀：/api/v3/knowledge
鉴权：Bearer Token（通过主项目 deps 获取 current_user）
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.knowledge import (
    AnnotationCreate,
    AnnotationOut,
    CitationExportRequest,
    CitationGraphOut,
    FolderCreate,
    FolderNode,
    KnowledgeSearchResult,
    LibraryPaperCreate,
    LibraryPaperOut,
    LibraryPaperUpdate,
    PaperMeta,
    ReadStatus,
    SearchScope,
)
from app.services.knowledge_service import KnowledgeService, _uuid_to_int

router = APIRouter()


def _user_id_int(user: User) -> int:
    """将主项目 UUID user_id 转为兼容 M3 API 的 int 型 ID。"""
    return _uuid_to_int(user.id)


def _build_library_out(entry) -> dict:
    """将主项目 UserLibrary ORM 对象转换为 M3 API 兼容的 LibraryPaperOut。

    Args:
        entry: app.models.library.UserLibrary 实例
    """
    paper = entry.paper
    paper_meta = None
    if paper:
        # 优先用 openalex_id 作为外部 paper_id，兜底用 UUID 字符串
        paper_id_str = getattr(paper, "openalex_id", None) or str(paper.id)
        paper_meta = PaperMeta(
            paper_id=paper_id_str,
            title=paper.title or "",
            authors=paper.authors if isinstance(paper.authors, list) else [],
            journal=getattr(paper, "journal", None),
            year=getattr(paper, "year", None),
            doi=getattr(paper, "doi", None),
            abstract=paper.abstract or None,
        )

    # read_status 映射: is_read (bool) → "unread"/"reading"/"finished"
    read_status = ReadStatus.finished if entry.is_read else ReadStatus.unread

    return {
        "id": _uuid_to_int(entry.id),
        "user_id": _uuid_to_int(entry.user_id),
        "paper": paper_meta.model_dump() if paper_meta else None,
        "folder": entry.folder_name,
        "tags": entry.tags if isinstance(entry.tags, list) else (list(entry.tags.keys()) if isinstance(entry.tags, dict) else []),
        "is_favorited": bool(entry.is_favorite),
        "read_status": read_status,
        "notes": None,  # 主项目 ORM 无 notes
        "added_at": entry.added_at,
        "last_read_at": None,  # 主项目 ORM 无 last_read_at
    }


# ── 文献 CRUD ─────────────────────────────────────


@router.post("/papers")
async def create_library_paper(
    data: LibraryPaperCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加文献到知识库。"""
    user_id = _user_id_int(current_user)
    try:
        entry = await KnowledgeService.add_paper(db, user_id, data)
    except ValueError as e:
        if str(e) == "DUPLICATE":
            raise ConflictError(message="文献已在知识库中")
        raise
    await KnowledgeService.record_read(db, user_id, _uuid_to_int(entry.id))
    return APIResponse(
        code=0,
        message="已添加到知识库",
        data=_build_library_out(entry),
    )


@router.get("/papers")
async def list_library_papers(
    folder: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    read_status: Optional[ReadStatus] = Query(None),
    is_favorited: Optional[bool] = Query(None),
    sort_by: str = Query("added_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库文献列表。"""
    user_id = _user_id_int(current_user)
    items, total = await KnowledgeService.list_papers(
        db, user_id, folder=folder, tag=tag, read_status=read_status,
        is_favorited=is_favorited, sort_by=sort_by, order=order,
        page=page, page_size=page_size,
    )
    return APIResponse(
        code=0,
        message="success",
        data={
            "items": [_build_library_out(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
    )


@router.get("/papers/{library_id:int}")
async def get_library_paper(
    library_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库单条文献详情。"""
    user_id = _user_id_int(current_user)
    entry = await KnowledgeService.get_paper(db, user_id, library_id)
    if not entry:
        raise NotFoundError(message="知识库条目不存在")
    return APIResponse(
        code=0,
        message="success",
        data=_build_library_out(entry),
    )


@router.put("/papers/{library_id:int}")
async def update_library_paper(
    library_id: int,
    data: LibraryPaperUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新知识库条目。"""
    user_id = _user_id_int(current_user)
    entry = await KnowledgeService.update_paper(db, user_id, library_id, data)
    if not entry:
        raise NotFoundError(message="知识库条目不存在")
    return APIResponse(
        code=0,
        message="已更新",
        data=_build_library_out(entry),
    )


@router.delete("/papers/{library_id:int}")
async def delete_library_paper(
    library_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从知识库移除文献。"""
    user_id = _user_id_int(current_user)
    deleted = await KnowledgeService.delete_paper(db, user_id, library_id)
    if not deleted:
        raise NotFoundError(message="知识库条目不存在")
    return APIResponse(code=0, message="已从知识库移除", data=None)


# ── 全文搜索 ─────────────────────────────────────


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1),
    search_in: SearchScope = Query(SearchScope.all),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全文搜索知识库文献。"""
    user_id = _user_id_int(current_user)
    items, total = await KnowledgeService.search(
        db, user_id, q, search_in, page, page_size
    )
    return APIResponse(
        code=0,
        message="success",
        data={
            "items": [
                {
                    "library_id": r.library_id,
                    "paper_title": r.paper_title,
                    "match_in": r.match_in,
                    "snippet": r.snippet,
                    "relevance_score": r.relevance_score,
                }
                for r in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


# ── 文件夹管理 ────────────────────────────────────


@router.get("/folders")
async def list_folders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件夹树。"""
    user_id = _user_id_int(current_user)
    tree = await KnowledgeService.get_folders(db, user_id)
    return APIResponse(
        code=0,
        message="success",
        data={"folders": [node.model_dump() for node in tree]},
    )


@router.post("/folders")
async def create_folder(
    data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建文件夹。"""
    user_id = _user_id_int(current_user)
    try:
        await KnowledgeService.create_folder(db, user_id, data.path)
    except ValueError:
        raise BadRequestError(message="无效的文件夹路径")
    return APIResponse(code=0, message="文件夹已创建", data={"path": data.path})


# ── 批注管理 ─────────────────────────────────────


@router.post("/annotations")
async def create_annotation(
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加批注。"""
    user_id = _user_id_int(current_user)
    entry = await KnowledgeService.get_paper(db, user_id, data.library_id)
    if not entry:
        raise NotFoundError(message="知识库条目不存在")
    try:
        annotation = await KnowledgeService.add_annotation(
            db, user_id, data.library_id,
            data.highlighted_text, data.note,
            data.position.model_dump() if data.position else None,
        )
    except ValueError:
        raise NotFoundError(message="知识库条目不存在")
    return APIResponse(
        code=0,
        message="批注已添加",
        data={
            "id": _uuid_to_int(annotation.id),
            "library_id": data.library_id,
            "highlighted_text": data.highlighted_text,
            "note": data.note,
            "position_data": annotation.highlight_range,
            "created_at": annotation.created_at.isoformat() if annotation.created_at else None,
        },
    )


@router.get("/annotations")
async def list_annotations(
    library_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定文献的所有批注。"""
    user_id = _user_id_int(current_user)
    annotations = await KnowledgeService.list_annotations(db, user_id, library_id)
    return APIResponse(
        code=0,
        message="success",
        data={
            "items": [
                {
                    "id": _uuid_to_int(a.id),
                    "library_id": library_id,
                    "highlighted_text": a.content or "",
                    "note": "",
                    "position_data": a.highlight_range,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in annotations
            ],
        },
    )


@router.delete("/annotations/{annotation_id:int}")
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除批注。"""
    user_id = _user_id_int(current_user)
    deleted = await KnowledgeService.delete_annotation(db, user_id, annotation_id)
    if not deleted:
        raise NotFoundError(message="批注不存在")
    return APIResponse(code=0, message="批注已删除", data=None)


# ── 引用导出 ─────────────────────────────────────


@router.post("/export-citation")
async def export_citation(
    data: CitationExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导出引用格式。"""
    from fastapi.responses import PlainTextResponse

    user_id = _user_id_int(current_user)
    citation_text = await KnowledgeService.export_citation(
        db, user_id, data.library_ids, data.format
    )
    return PlainTextResponse(
        content=citation_text, media_type="text/plain; charset=utf-8"
    )


# ── 引用图谱 ─────────────────────────────────────


@router.get("/citation-graph/{library_id:int}")
async def citation_graph(
    library_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取引用关系图谱。"""
    user_id = _user_id_int(current_user)
    graph = await KnowledgeService.citation_graph(db, user_id, library_id)
    return APIResponse(code=0, message="success", data=graph.model_dump())


# ── 阅读历史 ─────────────────────────────────────


@router.get("/reading-history")
async def reading_history(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取阅读历史。"""
    user_id = _user_id_int(current_user)
    history = await KnowledgeService.reading_history(db, user_id, days, limit)
    return APIResponse(
        code=0,
        message="success",
        data={
            "items": [_build_library_out(h) for h in history],
            "total": len(history),
        },
    )
