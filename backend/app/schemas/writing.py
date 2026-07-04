"""
M5 - AI写作辅助 Pydantic Schemas

请求/响应数据模型，统一使用 APIResponse 包装。
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ── 文献综述 ─────────────────────────────────

class ContentBlock(BaseModel):
    """P0-F: 内容块（支持 LaTeX / Mermaid 渲染）"""
    type: str = Field(..., description="块类型：text / latex / mermaid")
    content: str = Field(..., description="块内容")


class LiteratureReviewRequest(BaseModel):
    """文献综述生成请求"""
    library_ids: List[int] = Field(..., min_length=1, max_length=50)
    topic: Optional[str] = Field(None, description="综述主题")
    language: str = Field(default="zh", description="输出语言 zh/en")
    structure: Optional[List[str]] = Field(
        None, description="自定义结构，如 ['引言', '方法分类', '研究进展']"
    )


class SourcePaperInfo(BaseModel):
    paper_id: str
    title: str
    sections: List[str]


class LiteratureReviewResponse(BaseModel):
    document_id: str
    title: str
    content: str
    content_blocks: List[ContentBlock] = Field(default_factory=list, description="P0-F: 结构化内容块")
    ai_generated_ratio: float
    source_papers: List[SourcePaperInfo]
    status: str
    created_at: str


# ── 润色 ─────────────────────────────────────

class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待润色文本")
    language: str = Field(..., description="目标语言：zh / en")
    style: str = Field(default="academic", description="风格：academic / concise / elaborate")


class PolishResponse(BaseModel):
    original_text: str
    polished_text: str
    content_blocks: List[ContentBlock] = Field(default_factory=list, description="P0-F: 结构化内容块")
    changes_summary: str
    trace_id: str


# ── 降重 ─────────────────────────────────────

class RephraseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待降重文本")
    language: str = Field(..., description="语言：zh / en")
    intensity: str = Field(default="moderate", description="强度：light / moderate / aggressive")


class RephraseResponse(BaseModel):
    original_text: str
    rephrased_text: str
    content_blocks: List[ContentBlock] = Field(default_factory=list, description="P0-F: 结构化内容块")
    similarity_score: float
    changes_summary: str
    trace_id: str


# ── 期刊格式化 ──────────────────────────────

class FormatJournalRequest(BaseModel):
    document_id: str = Field(..., description="文档 ID")
    journal_name: str = Field(..., description="目标期刊名称")


class FormatJournalResponse(BaseModel):
    document_id: str
    journal: str
    changes: List[str]
    updated_at: str


# ── 引用插入 ─────────────────────────────────

class InsertCitationRequest(BaseModel):
    document_id: str = Field(..., description="文档 ID")
    library_ids: List[int] = Field(..., min_length=1)
    insert_position: int = Field(..., ge=0, description="插入位置偏移量")
    format: str = Field(default="numeric", description="引用格式：numeric / author_year")


class InsertCitationResponse(BaseModel):
    document_id: str
    inserted_citation: str
    references_appended: List[str]


# ── 溯源 ─────────────────────────────────────

class TracePaperInfo(BaseModel):
    paper_id: str
    title: str
    relevance: str


class TraceSegment(BaseModel):
    text: str
    is_ai_generated: bool
    source_papers: List[TracePaperInfo]


class TraceDetailResponse(BaseModel):
    document_id: str
    ai_generated_ratio: float
    segments: List[TraceSegment]


# ── 文档管理 ─────────────────────────────────

class WritingDocumentItem(BaseModel):
    document_id: str
    title: str
    status: str
    ai_generated_ratio: float
    updated_at: str


class WritingDocumentListResponse(BaseModel):
    items: List[WritingDocumentItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class WritingDocumentUpdateRequest(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None


class WritingDocumentUpdateResponse(BaseModel):
    document_id: str
    updated_at: str


# ── P0-A: 写作 Plan 模式 ─────────────────────

class PlanCreate(BaseModel):
    """创建写作计划请求"""
    topic: str = Field(..., min_length=1, max_length=500)
    style: Optional[str] = Field("academic", description="风格：academic / concise / elaborate")
    language: Optional[str] = Field("zh", description="输出语言：zh / en")
    reference_ids: Optional[List[int]] = Field(None, description="参考文献 ID 列表")


class SectionGenerate(BaseModel):
    """逐节生成确认"""
    confirm: bool = Field(True, description="确认生成此节")


class SectionSummary(BaseModel):
    """大纲中的节摘要"""
    section_id: str = Field(..., description="节 ID，如 s1")
    title: str
    summary: str
    estimated_words: int
    status: str = "pending"  # pending / generating / completed
    key_references: List[int] = Field(default_factory=list)


class PlanResponse(BaseModel):
    """写作计划响应"""
    plan_id: int
    topic: str
    title: str
    status: str
    style: str
    language: str
    sections: List[SectionSummary] = Field(default_factory=list)
    progress: dict = Field(default_factory=dict)  # {completed: int, total: int}
    created_at: str


class SectionResult(BaseModel):
    """逐节生成结果"""
    plan_id: int
    section_id: str
    title: str
    content: str
    trace_detail: Optional[dict] = Field(None, description="P0-D: 原子级溯源详情")
    status: str


class FinalizeResponse(BaseModel):
    """润色整合结果"""
    plan_id: int
    document_id: str
    title: str
    content: str
    trace_detail: Optional[dict] = Field(None, description="P0-D: 全文溯源详情")


# ── P0-D: 原子级溯源 ─────────────────────────

class SentenceTraceAnnotation(BaseModel):
    """单句溯源标注"""
    sentence: str
    ref_ids: List[int] = Field(default_factory=list)
    type: str  # direct_citation / method_from / conclusion_from / ai_synthesis / ai_original
    confidence: str  # high / medium / low


class AtomicTraceResponse(BaseModel):
    """原子级溯源响应"""
    document_id: str
    total_sentences: int
    traced_sentences: int
    source_summary: dict = Field(default_factory=dict)
    annotations: List[SentenceTraceAnnotation] = Field(default_factory=list)
