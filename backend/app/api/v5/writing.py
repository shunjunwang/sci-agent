"""
M5 - AI写作辅助 API 端点 (v5)

8 个端点，所有端点需要 get_current_user 依赖。
核心约束：溯源标记不可绕过——所有 AI 生成内容在服务层已经过 _ensure_trace_annotation 强制处理。
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.writing import (
    LiteratureReviewRequest, LiteratureReviewResponse,
    PolishRequest, PolishResponse,
    RephraseRequest, RephraseResponse,
    FormatJournalRequest, FormatJournalResponse,
    InsertCitationRequest, InsertCitationResponse,
    TraceDetailResponse,
    WritingDocumentListResponse, WritingDocumentItem,
    WritingDocumentUpdateRequest, WritingDocumentUpdateResponse,
    # P0-A: Plan 模式
    PlanCreate, PlanResponse, SectionGenerate, SectionResult, FinalizeResponse,
    # P0-D: 原子级溯源
    AtomicTraceResponse,
)
from app.services.writing_service import writing_service

router = APIRouter(dependencies=[Depends(get_current_user)])


def _make_request_id() -> str:
    return str(uuid.uuid4())


# ── POST /literature-review ──────────────────────

@router.post("/literature-review", response_model=APIResponse[LiteratureReviewResponse])
async def literature_review(
    req: LiteratureReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await writing_service.generate_literature_review(
            db=db,
            user_id=str(user.id),
            library_ids=req.library_ids,
            topic=req.topic,
            language=req.language,
            structure=req.structure,
        )
        return APIResponse[LiteratureReviewResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


# ── POST /polish ─────────────────────────────────

@router.post("/polish", response_model=APIResponse[PolishResponse])
async def polish(
    req: PolishRequest,
    user: User = Depends(get_current_user),
):
    result = await writing_service.polish_text(
        text=req.text, language=req.language, style=req.style,
    )
    return APIResponse[PolishResponse](
        code=0, message="success", data=result, request_id=_make_request_id(),
    )


# ── POST /rephrase ───────────────────────────────

@router.post("/rephrase", response_model=APIResponse[RephraseResponse])
async def rephrase(
    req: RephraseRequest,
    user: User = Depends(get_current_user),
):
    result = await writing_service.rephrase_text(
        text=req.text, language=req.language, intensity=req.intensity,
    )
    return APIResponse[RephraseResponse](
        code=0, message="success", data=result, request_id=_make_request_id(),
    )


# ── GET /documents/{document_id}/trace ────────────

@router.get("/documents/{document_id}/trace", response_model=APIResponse[TraceDetailResponse])
async def get_trace(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await writing_service.get_trace(
            db=db, user_id=str(user.id), document_id=document_id,
        )
        return APIResponse[TraceDetailResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise NotFoundError(message=str(e))


# ── POST /format-for-journal ─────────────────────

@router.post("/format-for-journal", response_model=APIResponse[FormatJournalResponse])
async def format_for_journal(
    req: FormatJournalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await writing_service.format_for_journal(
            db=db, user_id=str(user.id),
            document_id=req.document_id, journal_name=req.journal_name,
        )
        return APIResponse[FormatJournalResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise NotFoundError(message=str(e))


# ── POST /insert-citation ────────────────────────

@router.post("/insert-citation", response_model=APIResponse[InsertCitationResponse])
async def insert_citation(
    req: InsertCitationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await writing_service.insert_citation(
            db=db, user_id=str(user.id), document_id=req.document_id,
            library_ids=req.library_ids, insert_position=req.insert_position,
            fmt=req.format,
        )
        return APIResponse[InsertCitationResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


# ── GET /documents ───────────────────────────────

@router.get("/documents", response_model=APIResponse[WritingDocumentListResponse])
async def list_documents(
    status: Optional[str] = Query(None, description="筛选状态：draft/published/archived"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await writing_service.list_documents(
        db=db, user_id=str(user.id), status=status, page=page, page_size=page_size,
    )
    return APIResponse[WritingDocumentListResponse](
        code=0, message="success", data=result, request_id=_make_request_id(),
    )


# ── PUT /documents/{document_id} ─────────────────

@router.put("/documents/{document_id}", response_model=APIResponse[WritingDocumentUpdateResponse])
async def update_document(
    document_id: str,
    req: WritingDocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await writing_service.update_document(
            db=db, user_id=str(user.id), document_id=document_id,
            content=req.content, title=req.title,
        )
        return APIResponse[WritingDocumentUpdateResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise NotFoundError(message=str(e))


# ═══════════════════════════════════════════════════
# P0-A: 写作 Plan 模式端点
# ═══════════════════════════════════════════════════

@router.post("/plan", response_model=APIResponse[PlanResponse])
async def create_plan(
    req: PlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建写作计划，生成大纲供用户确认。"""
    try:
        result = await writing_service.create_plan(
            db=db,
            user_id=str(user.id),
            topic=req.topic,
            style=req.style or "academic",
            language=req.language or "zh",
            reference_ids=req.reference_ids,
        )
        return APIResponse[PlanResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


@router.get("/plan/{plan_id}", response_model=APIResponse[PlanResponse])
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查看写作计划状态与进度。"""
    from app.models.writing import WritingPlan

    plan = await db.get(WritingPlan, plan_id)
    if not plan or str(plan.user_id) != str(user.id):
        raise NotFoundError(message="计划不存在或无权访问")

    sections = plan.sections_json or []
    total = len(sections)
    completed = sum(1 for s in sections if s.get("status") == "completed")

    result = {
        "plan_id": plan.id,
        "topic": plan.topic,
        "title": plan.title,
        "status": plan.status,
        "style": plan.style,
        "language": plan.language,
        "sections": [
            {
                "section_id": s["id"],
                "title": s["title"],
                "summary": s.get("summary", ""),
                "estimated_words": s.get("estimated_words", 0),
                "status": s.get("status", "pending"),
                "key_references": s.get("key_references", []),
            }
            for s in sections
        ],
        "progress": {"completed": completed, "total": total},
        "created_at": plan.created_at.isoformat(),
    }
    return APIResponse[PlanResponse](
        code=0, message="success", data=result, request_id=_make_request_id(),
    )


@router.post("/plan/{plan_id}/sections/{section_id}/generate",
             response_model=APIResponse[SectionResult])
async def generate_section(
    plan_id: int,
    section_id: str,
    req: SectionGenerate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """逐节生成内容（需确认）。每节生成后自动走 P0-D 原子级溯源。"""
    if not req.confirm:
        raise BadRequestError(message="请确认后生成")

    try:
        result = await writing_service.generate_section(
            db=db, user_id=str(user.id), plan_id=plan_id, section_id=section_id,
        )
        return APIResponse[SectionResult](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


@router.post("/plan/{plan_id}/finalize", response_model=APIResponse[FinalizeResponse])
async def finalize_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """全部节确认后，整合全文 → 统一润色 → 返回完整 Document。"""
    try:
        result = await writing_service.finalize_plan(
            db=db, user_id=str(user.id), plan_id=plan_id,
        )
        return APIResponse[FinalizeResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


# ═══════════════════════════════════════════════════
# P0-D: 原子级溯源端点
# ═══════════════════════════════════════════════════

@router.get("/documents/{document_id}/atomic-trace",
            response_model=APIResponse[AtomicTraceResponse])
async def get_atomic_trace(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查询文档的原子级溯源报告（句子级拆分）。"""
    try:
        result = await writing_service.get_atomic_trace(
            db=db, user_id=str(user.id), document_id=document_id,
        )
        return APIResponse[AtomicTraceResponse](
            code=0, message="success", data=result, request_id=_make_request_id(),
        )
    except ValueError as e:
        raise NotFoundError(message=str(e))
