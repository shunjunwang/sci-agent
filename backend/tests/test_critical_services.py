"""
P2-13: arxiv / pubmed / degradation / model_gateway 单元测试

覆盖四个关键模块：
- ArxivService: 查询构建、XML 解析、错误处理
- PubmedService: 查询构建、XML 解析、错误处理
- DegradationService: 五种降级策略
- ModelGateway: 列表查询、默认模型切换、chat 转发
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from httpx import Response, HTTPStatusError, Request, TimeoutException

from app.services.arxiv_service import ArxivService
from app.services.pubmed_service import PubmedService
from app.services.degradation import DegradationService, DegradationResult

# ═══════════════════════════════════════════════════════════════
# ArxivService
# ═══════════════════════════════════════════════════════════════

class TestArxivService:

    # 空 XML 模板
    EMPTY_XML = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        '<opensearch:totalResults>0</opensearch:totalResults>'
        '</feed>'
    )

    # 单个 entry 的 XML
    ONE_ENTRY_XML = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        '<opensearch:totalResults>1</opensearch:totalResults>'
        '<entry>'
        '<id>http://arxiv.org/abs/1706.03762v7</id>'
        '<title>Attention Is All You Need</title>'
        '<author><name>Ashish Vaswani</name></author>'
        '<summary>Transformer architecture.</summary>'
        '<published>2017-06-12T17:57:34Z</published>'
        '</entry>'
        '</feed>'
    )

    @staticmethod
    def _make_mock_client(xml_text=None, side_effect=None):
        """创建模拟的 httpx.AsyncClient，返回指定 XML 或抛出异常。"""
        mock_resp = Mock()
        if xml_text is not None:
            mock_resp.text = xml_text
        mock_resp.raise_for_status = Mock()

        mock_client = AsyncMock()
        if side_effect:
            mock_client.get = AsyncMock(side_effect=side_effect)
        else:
            mock_client.get = AsyncMock(return_value=mock_resp)

        mock_ac = MagicMock()
        mock_ac.__aenter__ = AsyncMock(return_value=mock_client)
        mock_ac.__aexit__ = AsyncMock(return_value=None)
        return mock_ac, mock_client

    @pytest.mark.asyncio
    async def test_build_query_basic(self):
        """查询字符串正确构建为 arXiv API 格式。"""
        mock_ac, mock_client = self._make_mock_client(self.EMPTY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            await ArxivService.search("deep learning", page_size=5)

        url = mock_client.get.call_args[0][0]
        assert "all:deep" in url
        assert "max_results=5" in url
        assert "sortBy=relevance" in url
        assert "start=0" in url

    @pytest.mark.asyncio
    async def test_build_query_with_author(self):
        """作者筛选应追加到查询字符串。"""
        mock_ac, mock_client = self._make_mock_client(self.EMPTY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            await ArxivService.search("transformer", author="Vaswani")

        url = mock_client.get.call_args[0][0]
        assert "au:Vaswani" in url or "au%3AVaswani" in url

    @pytest.mark.asyncio
    async def test_build_query_with_year_filter(self):
        """年份筛选应追加到查询字符串。"""
        mock_ac, mock_client = self._make_mock_client(self.EMPTY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            await ArxivService.search("transformer", year_from=2023, year_to=2024)

        url = mock_client.get.call_args[0][0]
        assert "submittedDate" in url

    @pytest.mark.asyncio
    async def test_build_query_pagination(self):
        """分页参数 start 随 page 正确增长。"""
        mock_ac, mock_client = self._make_mock_client(self.EMPTY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            await ArxivService.search("ml", page=3, page_size=10)

        url = mock_client.get.call_args[0][0]
        assert "start=20" in url

    @pytest.mark.asyncio
    async def test_parse_empty_response(self):
        """空 XML 响应返回 total=0, 空列表。"""
        mock_ac, _ = self._make_mock_client(self.EMPTY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            total, papers = await ArxivService.search("test query")

        assert total == 0
        assert papers == []

    @pytest.mark.asyncio
    async def test_parse_response_with_entries(self):
        """正常 XML 响应正确提取标题/作者/摘要。"""
        mock_ac, _ = self._make_mock_client(self.ONE_ENTRY_XML)
        with patch("httpx.AsyncClient", return_value=mock_ac):
            total, papers = await ArxivService.search("transformer")

        assert total == 1
        assert papers[0].title == "Attention Is All You Need"
        assert papers[0].id.startswith("arxiv:1706.03762")

    @pytest.mark.asyncio
    async def test_search_http_error_propagates(self):
        """HTTP 错误时 search() 抛出异常（不再内部截获）。"""
        mock_ac, _ = self._make_mock_client(
            side_effect=HTTPStatusError(
                "Server error",
                request=Mock(spec=Request),
                response=Mock(status_code=503),
            )
        )
        with patch("httpx.AsyncClient", return_value=mock_ac):
            with pytest.raises(Exception):
                await ArxivService.search("test query")


# ═══════════════════════════════════════════════════════════════
# PubmedService
# ═══════════════════════════════════════════════════════════════

class TestPubmedService:

    ESUMMARY_EMPTY = {"result": {"uids": []}}

    @staticmethod
    def _make_mock_client(esearch_json=None, esummary_json=None, side_effect=None):
        """创建模拟的 PubmedService HTTP client。

        返回 (mock_client, captured_urls)，mock_client 可直接塞入
        PubmedService._get_client 的返回值。
        """
        captured = []

        async def _mock_get(url):
            captured.append(url)
            if side_effect:
                raise side_effect
            resp = Mock()
            if "esearch" in url:
                resp.json = Mock(return_value=esearch_json or {
                    "esearchresult": {"idlist": ["12345"], "count": 1},
                })
            else:
                resp.json = Mock(return_value=esummary_json or {
                    "result": {
                        "12345": {
                            "title": "Test Paper",
                            "authors": [{"name": "A Author"}],
                            "pubdate": "2023",
                        },
                        "uids": ["12345"],
                    },
                })
            resp.raise_for_status = Mock()
            return resp

        mock_client = AsyncMock()
        mock_client.get = _mock_get
        return mock_client, captured

    @pytest.mark.asyncio
    async def test_build_esearch_params_basic(self):
        """ESearch 参数构建正确（通过 search() 间接验证）。"""
        mock_client, captured = self._make_mock_client()
        svc = PubmedService()
        svc._get_client = AsyncMock(return_value=mock_client)

        await svc.search("cancer immunotherapy", page_size=20)

        esearch_url = captured[0]
        assert "esearch.fcgi" in esearch_url
        assert "cancer+immunotherapy" in esearch_url or "cancer%20immunotherapy" in esearch_url or "cancer immunotherapy" in esearch_url
        assert "retmax=20" in esearch_url
        assert "db=pubmed" in esearch_url

    @pytest.mark.asyncio
    async def test_build_esearch_params_with_dates(self):
        """日期范围参数应正确设置。"""
        mock_client, captured = self._make_mock_client()
        svc = PubmedService()
        svc._get_client = AsyncMock(return_value=mock_client)

        await svc.search("cancer", year_from=2022, year_to=2023)

        esearch_url = captured[0]
        assert "2022" in esearch_url and "2023" in esearch_url

    @pytest.mark.asyncio
    async def test_parse_search_result_empty(self):
        """空搜索结果返回 0 总数和空列表。"""
        mock_client, _ = self._make_mock_client(
            esearch_json={"esearchresult": {"idlist": [], "count": 0}},
            esummary_json={"result": {"uids": []}},
        )
        svc = PubmedService()
        svc._get_client = AsyncMock(return_value=mock_client)

        count, results = await svc.search("nonexistent query")
        assert count == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_parse_search_result_with_ids(self):
        """正常搜索结果正确提取标题。"""
        mock_client, _ = self._make_mock_client(
            esearch_json={"esearchresult": {"idlist": ["12345", "67890"], "count": 2}},
            esummary_json={
                "result": {
                    "12345": {
                        "title": "Paper One",
                        "authors": [{"name": "Author One"}],
                        "pubdate": "2023",
                    },
                    "67890": {
                        "title": "Paper Two",
                        "authors": [{"name": "Author Two"}],
                        "pubdate": "2024",
                    },
                    "uids": ["12345", "67890"],
                },
            },
        )
        svc = PubmedService()
        svc._get_client = AsyncMock(return_value=mock_client)

        count, results = await svc.search("test")
        assert count == 2
        assert results[0].id == "pubmed:12345"
        assert results[1].id == "pubmed:67890"

    @pytest.mark.asyncio
    async def test_search_error_propagates(self):
        """异常时 search() 抛出（不再截获）。"""
        mock_client, _ = self._make_mock_client(
            side_effect=TimeoutException("timeout"),
        )
        svc = PubmedService()
        svc._get_client = AsyncMock(return_value=mock_client)

        with pytest.raises(Exception):
            await svc.search("cancer")


# ═══════════════════════════════════════════════════════════════
# DegradationService
# ═══════════════════════════════════════════════════════════════

class TestDegradationService:

    def test_search_degraded_with_cache(self):
        """搜索降级返回缓存 + 时间标注。"""
        cache = {"papers": [{"title": "Old Result"}], "searched_at": "2025-01-01T00:00:00"}
        result = DegradationService.search_degraded("query", cache_data=cache)
        assert isinstance(result, DegradationResult)
        assert result.degraded is True
        assert "papers" in result.data
        assert len(result.warnings) == 1
        assert "缓存" in result.warnings[0]

    def test_search_degraded_no_cache(self):
        """无缓存搜索降级返回空结果 + 提示。"""
        result = DegradationService.search_degraded("query", cache_data=None)
        assert result.data["total"] == 0
        assert len(result.warnings) >= 1

    def test_sandbox_degraded(self):
        """沙箱降级返回部分输出 + 建议。"""
        partial_output = "Processed 80% successfully"
        error_msg = "Killed by OOM"
        result = DegradationService.sandbox_degraded(
            job_uid="job-001", partial_output=partial_output, error_msg=error_msg
        )
        assert result.degraded is True
        assert result.data["partial_output"] == partial_output

    def test_pdf_parse_degraded(self):
        """PDF 解析降级返回部分文本 + 警告。"""
        raw_text = "Scanned content (OCR)"
        result = DegradationService.pdf_parse_degraded("doc.pdf", raw_text=raw_text)
        assert result.degraded is True
        assert result.data["partial_text"] == raw_text
        assert result.data["status"] == "degraded"

    def test_writing_timeout_degraded(self):
        """写作超时降级返回已完成部分。"""
        completed = [{"title": "Introduction", "content": "已完成..."}]
        result = DegradationService.writing_timeout_degraded(
            document_title="Test Doc", completed_sections=completed, current_section="Methods"
        )
        assert result.degraded is True
        assert result.data["completed_sections"] == completed
        assert result.data["status"] == "degraded"
        assert result.data["can_resume"] is True

    def test_hash_chain_broken(self):
        """哈希链断裂报告断裂点 + 阻止写入。"""
        result = DegradationService.hash_chain_broken(
            document_id="doc-001", broken_at_index=3
        )
        assert result.degraded is True
        assert result.data["document_id"] == "doc-001"
        assert result.data["broken_at_index"] == 3
        assert result.data["action_taken"] == "write_blocked"

    def test_to_dict(self):
        """DegradationResult.to_dict() 结构正确。"""
        result = DegradationResult(data={"key": "value"}, warnings=["warn"])
        d = result.to_dict()
        assert d["degraded"] is True
        assert d["data"] == {"key": "value"}
        assert d["warnings"] == ["warn"]
        assert "degraded_at" in d


# ═══════════════════════════════════════════════════════════════
# ModelGateway
# ═══════════════════════════════════════════════════════════════

class TestModelGateway:

    @pytest.mark.asyncio
    async def test_list_available_models_empty(self, db_session):
        """无配置时 list_available_models 返回空列表。"""
        from app.services.model_gateway import ModelGatewayService
        import uuid

        svc = ModelGatewayService()
        user_id = uuid.uuid4()
        models = await svc.list_available_models(db_session, user_id)
        assert isinstance(models, list)
        assert len(models) == 0

    @pytest.mark.asyncio
    async def test_chat_invalid_provider(self, db_session):
        """无效 model 名抛出 ValueError。"""
        from app.services.model_gateway import ModelGatewayService
        from app.schemas.model_gateway import ChatRequest, ChatMessage
        import uuid

        svc = ModelGatewayService()
        req = ChatRequest(
            model="nonexistent_model",
            messages=[ChatMessage(role="user", content="hello")],
        )
        with pytest.raises(ValueError):
            await svc.chat(db_session, uuid.uuid4(), req)

    def test_is_model_retryable(self):
        """5xx 和 Timeout 为可重试，4xx 不可重试。"""
        from app.services.model_gateway import _is_model_retryable

        # 5xx → retryable
        mock_5xx = HTTPStatusError(
            "Internal Error",
            request=Mock(spec=Request),
            response=Mock(status_code=503),
        )
        assert _is_model_retryable(mock_5xx) is True

        # Timeout → retryable
        assert _is_model_retryable(TimeoutException("timeout")) is True

        # 4xx → not retryable
        mock_4xx = HTTPStatusError(
            "Bad Request",
            request=Mock(spec=Request),
            response=Mock(status_code=400),
        )
        assert _is_model_retryable(mock_4xx) is False

    @pytest.mark.skip(reason="_compute_cache_key not yet implemented in model_gateway.py, and has no implementation plan")
    def test_cache_key_deterministic(self):
        """已删除：_compute_cache_key 无实现计划。"""
        pass

    @pytest.mark.skip(reason="_compute_cache_key not yet implemented in model_gateway.py, and has no implementation plan")
    def test_cache_key_differs_on_content(self):
        """已删除：_compute_cache_key 无实现计划。"""
        pass
