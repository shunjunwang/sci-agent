"""
P0-K: 学术规范自查 API

端点：
- POST /api/v1/academic-check/format      — 参考文献格式检查
- POST /api/v1/academic-check/structure   — 论文章节结构检查
- POST /api/v1/academic-check/citations   — 引用完整性双向校验
"""
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.services.academic_checker_service import academic_checker_service

router = APIRouter(prefix="/academic-check", tags=["Academic Checker"], dependencies=[Depends(get_current_user)])


# ── 请求模型 ───────────────────────────────────────


class FormatCheckRequest(BaseModel):
    """参考文献格式检查请求。"""
    references: List[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="参考文献列表，每项为一条完整的引文字符串",
    )
    style: str = Field(
        default="gbt7714",
        description="目标格式规范：gbt7714 / apa / mla",
    )


class StructureCheckRequest(BaseModel):
    """论文章节结构检查请求。"""
    headings: List[str] = Field(
        ...,
        min_length=1,
        max_length=200,
        description="论文各级标题列表",
    )


class CitationCheckRequest(BaseModel):
    """引用完整性校验请求。"""
    text: str = Field(
        ...,
        min_length=1,
        description="论文正文内容（含引用标记）",
    )
    references: List[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="参考文献列表",
    )
    style: str = Field(
        default="numeric",
        description="引用风格：numeric / author_year",
    )


# ── 响应模型 ───────────────────────────────────────


class CheckIssueResponse(BaseModel):
    """单个问题响应。"""
    severity: str
    message: str
    location: str
    suggestion: str


class CheckResultResponse(BaseModel):
    """检查结果响应。"""
    passed: bool
    total_checks: int
    passed_checks: int
    errors: List[CheckIssueResponse]
    warnings: List[CheckIssueResponse]
    summary: str


# ── API 端点 ───────────────────────────────────────


@router.post("/format", response_model=CheckResultResponse)
async def check_reference_format(
    req: FormatCheckRequest,
    _user: dict = Depends(get_current_user),
) -> CheckResultResponse:
    """检查参考文献格式是否符合指定规范（GB/T 7714 / APA / MLA）。

    对每条参考文献进行正则模式匹配，检查：
    - 基本格式结构（作者、题名、刊名、年份等要素）
    - 出版年份是否缺失
    - 空引用是否误入
    """
    result = academic_checker_service.check_format(
        references=req.references,
        style=req.style,
    )
    return CheckResultResponse(
        passed=result.passed,
        total_checks=result.total_checks,
        passed_checks=result.passed_checks,
        errors=[
            CheckIssueResponse(
                severity=e.severity,
                message=e.message,
                location=e.location,
                suggestion=e.suggestion,
            )
            for e in result.errors
        ],
        warnings=[
            CheckIssueResponse(
                severity=w.severity,
                message=w.message,
                location=w.location,
                suggestion=w.suggestion,
            )
            for w in result.warnings
        ],
        summary=result.summary,
    )


@router.post("/structure", response_model=CheckResultResponse)
async def check_paper_structure(
    req: StructureCheckRequest,
    _user: dict = Depends(get_current_user),
) -> CheckResultResponse:
    """检查论文章节结构是否完整。

    检查是否包含学术论文必需的 5 个核心章节：
    引言、方法、结果、讨论、结论。
    以及推荐的 4 个辅助章节：摘要、相关工作、致谢、参考文献。
    支持中英文标题识别。
    """
    result = academic_checker_service.check_structure(
        headings=req.headings,
    )
    return CheckResultResponse(
        passed=result.passed,
        total_checks=result.total_checks,
        passed_checks=result.passed_checks,
        errors=[
            CheckIssueResponse(
                severity=e.severity,
                message=e.message,
                location=e.location,
                suggestion=e.suggestion,
            )
            for e in result.errors
        ],
        warnings=[
            CheckIssueResponse(
                severity=w.severity,
                message=w.message,
                location=w.location,
                suggestion=w.suggestion,
            )
            for w in result.warnings
        ],
        summary=result.summary,
    )


@router.post("/citations", response_model=CheckResultResponse)
async def check_citation_integrity(
    req: CitationCheckRequest,
    _user: dict = Depends(get_current_user),
) -> CheckResultResponse:
    """双向校验引用完整性。

    检查：
    1. 正文引用了但参考文献列表未收录的「孤儿引用」
    2. 参考文献列表中有但正文未引用的「未引用文献」
    3. （数字型）引用编号是否连续

    支持数字型引用 [1]、[1,2] 以及作者-年份引用 (Author, 2020)。
    """
    result = academic_checker_service.check_citations(
        text=req.text,
        references=req.references,
        style=req.style,
    )
    return CheckResultResponse(
        passed=result.passed,
        total_checks=result.total_checks,
        passed_checks=result.passed_checks,
        errors=[
            CheckIssueResponse(
                severity=e.severity,
                message=e.message,
                location=e.location,
                suggestion=e.suggestion,
            )
            for e in result.errors
        ],
        warnings=[
            CheckIssueResponse(
                severity=w.severity,
                message=w.message,
                location=w.location,
                suggestion=w.suggestion,
            )
            for w in result.warnings
        ],
        summary=result.summary,
    )
