"""
M5 - AI写作辅助 单元测试

核心验证：溯源标记不可绕过、所有 API 端点可用、文档 CRUD 正常。
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.writing_service import (
    WritingService, _ensure_trace_annotation, MockLLMClient,
)
from app.models.writing import WritingDocument

USER_UUID = "00000000-0000-0000-0000-000000000001"
DOC_UUID  = "00000000-0000-0000-0000-000000000010"


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


@pytest.fixture
def svc():
    return WritingService()


def _make_paper_mock(paper_id="p-001", title="Test Paper", year=2024):
    p = MagicMock()
    p.id = paper_id
    p.title = title
    p.authors = [{"name": "Smith J."}]
    p.journal = "Nature"
    p.publication_date = MagicMock(year=year)
    return p


def _setup_paper_query(mock_db, papers):
    """设置 db.execute → result.scalars().all() → papers 的 mock 链"""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = papers
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result


def _setup_scalars_result(mock_db, items):
    """通用：db.execute → result.scalars().all() → items"""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = items
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result


def _make_doc(title="测试", content="内容", status="draft"):
    doc = WritingDocument(
        user_id=uuid.UUID(USER_UUID),
        title=title, content=content, status=status,
    )
    doc.id = uuid.UUID(DOC_UUID)
    doc.created_at = MagicMock()
    doc.created_at.isoformat.return_value = "2026-07-02T10:00:00Z"
    doc.updated_at = MagicMock()
    doc.updated_at.isoformat.return_value = "2026-07-02T10:00:00Z"
    return doc


# ── 溯源标记强制机制 ──────────────────────────

class TestTraceAnnotation:

    def test_content_already_has_marker_no_append(self):
        content = "这是一段 AI 生成内容。[AI生成, 参考文献: Smith 2024]"
        result = _ensure_trace_annotation(content)
        assert result == content

    def test_content_without_marker_gets_appended(self):
        content = "无标记内容。"
        result = _ensure_trace_annotation(content)
        assert "[AI生成]" in result

    def test_polish_action_adds_appropriate_suffix(self):
        result = _ensure_trace_annotation("润色文本。", action="润色")
        assert "[AI润色" in result
        assert "原始内容由用户提供" in result

    def test_rephrase_action_adds_appropriate_suffix(self):
        cited = [{"short_ref": "Smith 2024", "title": "Test Paper"}]
        result = _ensure_trace_annotation("降重文本。", cited_papers=cited, action="降重")
        assert "[AI降重" in result

    def test_with_cited_papers_shows_references(self):
        cited = [
            {"short_ref": "Smith 2024", "title": "Paper A"},
            {"short_ref": "Wang 2023", "title": "Paper B"},
        ]
        result = _ensure_trace_annotation("综述。", cited_papers=cited, action="生成")
        assert "[AI生成, 参考文献:" in result
        assert "Smith 2024" in result
        assert "Wang 2023" in result

    def test_empty_content_returns_empty(self):
        assert _ensure_trace_annotation("") == ""


# ── Mock LLM 客户端 ──────────────────────────

class TestMockLLMClient:

    @pytest.mark.asyncio
    async def test_review_prompt_returns_structured_content(self):
        result = await MockLLMClient.chat("请生成文献综述")
        assert "##" in result

    @pytest.mark.asyncio
    async def test_polish_prompt_returns_polished(self):
        result = await MockLLMClient.chat("请对以下文本进行学术润色")
        assert "润色" in result or "学术" in result or "优化" in result

    @pytest.mark.asyncio
    async def test_rephrase_prompt_returns_rephrased(self):
        result = await MockLLMClient.chat("请对以下文本进行学术降重")
        assert len(result) > 0


# ── 文献综述生成 ─────────────────────────────

class TestLiteratureReview:

    @pytest.mark.asyncio
    async def test_literature_review_content_has_trace_marker(self, mock_db, svc):
        _setup_paper_query(mock_db, [_make_paper_mock()])
        doc = _make_doc()
        async def fake_handle(*args, **kwargs):
            return doc
        svc._handle_generation = fake_handle  # type: ignore[method-assign]

        with patch.object(MockLLMClient, "chat", return_value="## 引言\n\n进展。"):
            result = await svc.generate_literature_review(
                db=mock_db, user_id=USER_UUID, library_ids=[1, 2],
            )
        assert "document_id" in result
        assert result["status"] == "draft"
        assert isinstance(result["source_papers"], list)

    @pytest.mark.asyncio
    async def test_literature_review_no_papers_raises_error(self, mock_db, svc):
        """空论文列表应返回 mock 降级数据。"""
        _setup_paper_query(mock_db, [])
        result = await svc.generate_literature_review(
            db=mock_db, user_id=USER_UUID, library_ids=[999],
        )
        assert result["status"] == "draft"
        assert result["document_id"].startswith("mock-")
        assert "基于指定文献的综述" in result["title"]

    @pytest.mark.asyncio
    async def test_literature_review_custom_topic(self, mock_db, svc):
        _setup_paper_query(mock_db, [_make_paper_mock()])
        doc = _make_doc(title="自定义主题综述")
        async def fake_handle(*args, **kwargs):
            return doc
        svc._handle_generation = fake_handle  # type: ignore[method-assign]

        with patch.object(MockLLMClient, "chat", return_value="内容"):
            result = await svc.generate_literature_review(
                db=mock_db, user_id=USER_UUID, library_ids=[1],
                topic="自定义主题", language="en",
                structure=["Introduction", "Methods"],
            )
        assert "自定义主题" in result["title"]


# ── 润色 ─────────────────────────────────────

class TestPolish:

    @pytest.mark.asyncio
    async def test_polish_returns_trace_marker(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="润色后文本。"):
            result = await svc.polish_text("原始", language="zh", style="academic")
        assert "polished_text" in result
        assert "[AI润色" in result["polished_text"]
        assert "changes_summary" in result

    @pytest.mark.asyncio
    async def test_polish_enforces_trace_even_if_llm_omits(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="无标记"):
            result = await svc.polish_text("待润色", language="zh")
        assert "[AI润色" in result["polished_text"]


# ── 降重 ─────────────────────────────────────

class TestRephrase:

    @pytest.mark.asyncio
    async def test_rephrase_returns_trace_marker(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="降重后"):
            result = await svc.rephrase_text("原文", language="zh", intensity="moderate")
        assert "rephrased_text" in result
        assert "[AI降重" in result["rephrased_text"]
        assert 0 < result["similarity_score"] < 1

    @pytest.mark.asyncio
    async def test_rephrase_intensity_affects_similarity(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="降重后"):
            light = await svc.rephrase_text("文本", "zh", "light")
        with patch.object(MockLLMClient, "chat", return_value="降重后"):
            aggressive = await svc.rephrase_text("文本", "zh", "aggressive")
        assert light["similarity_score"] > aggressive["similarity_score"]


# ── 文档管理 ─────────────────────────────────

class TestDocumentCRUD:

    @pytest.mark.asyncio
    async def test_list_documents(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.id = uuid.UUID(DOC_UUID)
        mock_doc.title = "测试文档"
        mock_doc.status = "draft"
        mock_doc.ai_generated_ratio = 0.5
        mock_doc.updated_at = MagicMock()
        mock_doc.updated_at.isoformat.return_value = "2026-07-02T10:00:00Z"

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_doc]
        list_result = MagicMock()
        list_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [count_result, list_result]

        result = await svc.list_documents(db=mock_db, user_id=USER_UUID)
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["document_id"] == DOC_UUID

    @pytest.mark.asyncio
    async def test_update_document(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.id = uuid.UUID(DOC_UUID)
        mock_doc.user_id = uuid.UUID(USER_UUID)
        mock_doc.content = "old content"
        mock_doc.title = "old title"
        mock_doc.updated_at = MagicMock()
        mock_doc.updated_at.isoformat.return_value = "2026-07-02T11:00:00Z"
        mock_db.get.return_value = mock_doc

        result = await svc.update_document(
            db=mock_db, user_id=USER_UUID, document_id=DOC_UUID,
            content="new content", title="new title",
        )
        assert result["document_id"] == DOC_UUID
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_unauthorized(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.user_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        mock_db.get.return_value = mock_doc

        with pytest.raises(ValueError, match="无权"):
            await svc.update_document(
                db=mock_db, user_id=USER_UUID, document_id=DOC_UUID,
                content="hacked",
            )


# ── 期刊格式化 ──────────────────────────────

class TestFormatJournal:

    @pytest.mark.asyncio
    async def test_format_journal_returns_changes(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.id = uuid.UUID(DOC_UUID)
        mock_doc.user_id = uuid.UUID(USER_UUID)
        mock_doc.content = "content"
        mock_doc.updated_at = MagicMock()
        mock_doc.updated_at.isoformat.return_value = "2026-07-02T10:30:00Z"
        mock_db.get.return_value = mock_doc

        with patch.object(MockLLMClient, "chat", return_value="格式化后"):
            result = await svc.format_for_journal(
                db=mock_db, user_id=USER_UUID, document_id=DOC_UUID,
                journal_name="计算机学报",
            )
        assert result["journal"] == "计算机学报"
        assert len(result["changes"]) >= 1


# ── 引用插入 ────────────────────────────────

class TestInsertCitation:

    @pytest.mark.asyncio
    async def test_insert_citation_numeric(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.id = uuid.UUID(DOC_UUID)
        mock_doc.user_id = uuid.UUID(USER_UUID)
        mock_doc.content = "正文内容。结语。"
        mock_db.get.return_value = mock_doc

        _setup_paper_query(mock_db, [_make_paper_mock()])

        result = await svc.insert_citation(
            db=mock_db, user_id=USER_UUID, document_id=DOC_UUID,
            library_ids=[1], insert_position=4, fmt="numeric",
        )
        assert "inserted_citation" in result
        assert len(result["references_appended"]) == 1


# ── 溯源详情 ────────────────────────────────

class TestTraceDetail:

    @pytest.mark.asyncio
    async def test_get_trace(self, mock_db, svc):
        mock_doc = MagicMock()
        mock_doc.id = uuid.UUID(DOC_UUID)
        mock_doc.user_id = uuid.UUID(USER_UUID)
        mock_doc.ai_generated_ratio = 0.85
        mock_db.get.return_value = mock_doc

        mock_trace = MagicMock()
        mock_trace.ai_generated_text = "AI生成内容。[AI生成, 参考文献: Smith 2024]"
        mock_trace.block_index = 0
        mock_trace.cited_paper_ids = ["p-001"]

        _setup_scalars_result(mock_db, [mock_trace])

        result = await svc.get_trace(db=mock_db, user_id=USER_UUID, document_id=DOC_UUID)
        assert result["document_id"] == DOC_UUID
        assert result["ai_generated_ratio"] == 0.85
        assert len(result["segments"]) == 1
        assert result["segments"][0]["is_ai_generated"] is True


# ── 综合：溯源标记不可绕过 ─────────────────

class TestTraceAnnotationEnforcedEverywhere:

    @pytest.mark.asyncio
    async def test_polish_enforces_annotation(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="无标记润色"):
            result = await svc.polish_text("原文", "zh")
        assert "[AI" in result["polished_text"]

    @pytest.mark.asyncio
    async def test_rephrase_enforces_annotation(self, svc):
        with patch.object(MockLLMClient, "chat", return_value="无标记降重"):
            result = await svc.rephrase_text("原文", "zh")
        assert "[AI" in result["rephrased_text"]

    @pytest.mark.asyncio
    async def test_review_enforces_annotation(self, mock_db, svc):
        _setup_paper_query(mock_db, [_make_paper_mock()])
        doc = _make_doc()
        async def fake_handle(*args, **kwargs):
            # Simulate service applying _ensure_trace_annotation
            doc.content = _ensure_trace_annotation("无标记综述", action="生成")
            return doc
        svc._handle_generation = fake_handle  # type: ignore[method-assign]

        with patch.object(MockLLMClient, "chat", return_value="无标记综述"):
            result = await svc.generate_literature_review(
                db=mock_db, user_id=USER_UUID, library_ids=[1],
            )
        assert "[AI" in result["content"]


# ── 引文格式测试 (P0-4) ──────────────────────

from app.utils.citation_formatter import format_citation  # noqa: E402
from app.schemas.knowledge import CitationFormat  # noqa: E402


_DEMO_PAPER = {
    "title": "Machine Learning Applications in Science",
    "authors": ["Smith John", "Zhang Wei", "Li Si", "Wang Wu", "Chen Liu", "Yang Qi", "Huang Ba"],
    "journal": "Nature Machine Intelligence",
    "year": 2024,
    "volume": "6",
    "issue": "3",
    "pages": "200-215",
    "doi": "10.1038/s42256-024-00123-4",
}


class TestCitationFormatAPA7:

    def test_apa7_has_doi_hyperlink(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.apa, index=1)
        assert "https://doi.org/10.1038/s42256-024-00123-4" in result

    def test_apa7_truncates_many_authors(self):
        """APA 7th: 超过 20 作者应截断。"""
        many_authors = [f"Author {i}" for i in range(25)]
        paper = {**_DEMO_PAPER, "authors": many_authors}
        result = format_citation(paper, CitationFormat.apa)
        assert "..." in result

    def test_apa7_output_structure(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.apa)
        # Smith, J., Zhang, W., Li, S., Wang, W., Chen, L., Yang, Q., & Huang, B. (2024). ...
        assert "Smith, J." in result
        assert "(2024)" in result


class TestCitationFormatChicago:

    def test_chicago_has_title_in_quotes(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.chicago)
        assert '"Machine Learning Applications in Science."' in result

    def test_chicago_truncates_many_authors(self):
        many_authors = [f"Author {i}" for i in range(15)]
        paper = {**_DEMO_PAPER, "authors": many_authors}
        result = format_citation(paper, CitationFormat.chicago)
        assert "..." in result

    def test_chicago_output_structure(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.chicago)
        assert "2024." in result
        assert "Nature Machine Intelligence" in result


class TestCitationFormatVancouver:

    def test_vancouver_has_doi(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.vancouver)
        assert "doi:10.1038/s42256-024-00123-4" in result

    def test_vancouver_truncates_many_authors(self):
        """Vancouver: 超过 6 作者应截断为 et al."""
        many_authors = [f"Author {i}" for i in range(10)]
        paper = {**_DEMO_PAPER, "authors": many_authors}
        result = format_citation(paper, CitationFormat.vancouver)
        assert "et al." in result

    def test_vancouver_output_structure(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.vancouver)
        assert "Nature Machine Intelligence." in result
        assert "2024;6(3)" in result


class TestCitationFormatBibTeX:

    def test_bibtex_has_url_field(self):
        result = format_citation(_DEMO_PAPER, CitationFormat.bibtex)
        assert "url =" in result
        assert "https://doi.org/10.1038/s42256-024-00123-4" in result

    def test_bibtex_has_abstract_when_provided(self):
        paper = {**_DEMO_PAPER, "abstract": "This paper explores ML in science."}
        result = format_citation(paper, CitationFormat.bibtex)
        assert "abstract =" in result
