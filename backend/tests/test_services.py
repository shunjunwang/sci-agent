"""
PC2 M2 服务层单元测试
科应测试使用 mock（避免依赖网络和真实凭证）
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.cnki_service import CNKIService
from app.services.keying_service import KeyingService
from app.services.search_service import SearchService
from app.core.cli_manager import CLIServiceRegistry, cli_registry


# ---- 科应 Mock 数据（模拟 keying-cli 返回） ----
MOCK_KEYING_SEARCH_RESULT = [
    {
        "srid": "SR-MOCK-001",
        "originalTitle": "Deep Learning for NLP",
        "chineseTitle": "深度学习在自然语言处理中的应用",
        "originalAuthors": ["Alice", "Bob"],
        "chineseAbstract": "本文综述了深度学习在NLP中的最新进展。",
        "publicationDate": "2024-01-15",
        "doi": "10.1234/mock.001",
        "dataSource": "Nature",
        "featuredTags": ["1区", "A类期刊"],
        "hasPdf": True,
        "docType": "papers",
    }
]

MOCK_KEYING_DETAIL = {
    "srid": "SR-MOCK-001",
    "originalTitle": "Deep Learning for NLP",
    "chineseTitle": "深度学习在自然语言处理中的应用",
    "originalAuthors": ["Alice", "Bob"],
    "chineseAbstract": "本文综述了深度学习在NLP中的最新进展。",
    "publicationDate": "2024-01-15",
    "doi": "10.1234/mock.001",
    "dataSource": "Nature",
    "featuredTags": ["1区", "A类期刊"],
    "hasPdf": True,
    "docType": "papers",
    "volume": 12,
    "issue": 3,
    "startPage": 100,
    "endPage": 115,
    "refIds": ["SR-REF-001"],
}


@pytest.fixture
def mock_keying_client():
    """Mock keying-cli 的 ScienceRiverClient"""
    mock_client = MagicMock()
    mock_client.search.return_value = (MOCK_KEYING_SEARCH_RESULT, 42)
    mock_client.get_basic_info.return_value = MOCK_KEYING_DETAIL
    mock_client.get_pdf_url.return_value = "https://picture-m.scienceing.com/pdforiginal/mock.pdf"
    return mock_client


# ---- CNKI 测试（纯本地 Mock，无需外部依赖） ----

@pytest.mark.asyncio
async def test_cnki_search():
    """测试 CNKI 搜索"""
    total, results = await CNKIService.search("深度学习", page=1, page_size=10)
    assert total >= 0
    assert isinstance(results, list)
    if results:
        assert results[0].source == "cnki"


@pytest.mark.asyncio
async def test_cnki_search_with_author():
    """测试 CNKI 作者过滤"""
    total, results = await CNKIService.search("自然语言处理", author="张三")
    assert total >= 0
    for r in results:
        assert "张三" in r.authors


@pytest.mark.asyncio
async def test_cnki_search_with_year():
    """测试 CNKI 年份过滤"""
    total, results = await CNKIService.search("深度学习", year_from=2024, year_to=2024)
    assert total >= 0
    for r in results:
        if r.published_at:
            year_str = str(r.published_at)
            year = int(year_str[:4])
            assert 2024 <= year <= 2024


@pytest.mark.asyncio
async def test_cnki_detail():
    """测试 CNKI 详情"""
    detail = await CNKIService.get_detail("cnki:CNKI-12345")
    assert detail is not None
    assert detail.id == "cnki:CNKI-12345"
    assert detail.title == "基于深度学习的自然语言处理研究综述"


@pytest.mark.asyncio
async def test_cnki_detail_not_found():
    """测试 CNKI 不存在的文献"""
    detail = await CNKIService.get_detail("cnki:NOT-EXIST")
    assert detail is None


@pytest.mark.asyncio
async def test_cnki_pdf_url():
    """测试 CNKI PDF URL"""
    url = await CNKIService.get_pdf_url("cnki:CNKI-12345")
    assert url is not None
    assert "cnki.net" in url


# ---- 科应测试（Mock keying-cli） ----

@pytest.mark.asyncio
async def test_keying_search(mock_keying_client):
    """测试科应搜索（mock）"""
    with patch.object(KeyingService, "_get_client", return_value=mock_keying_client):
        total, results = await KeyingService.search("深度学习", page=1, page_size=10)
    assert total == 42
    assert len(results) == 1
    assert results[0].source == "keying"
    assert "深度学习" in results[0].title
    assert results[0].id == "keying:SR-MOCK-001"


@pytest.mark.asyncio
async def test_keying_detail(mock_keying_client):
    """测试科应详情（mock）"""
    with patch.object(KeyingService, "_get_client", return_value=mock_keying_client):
        detail = await KeyingService.get_detail("keying:SR-MOCK-001")
    assert detail is not None
    assert detail.id == "keying:SR-MOCK-001"
    assert detail.journal == "Nature"
    assert detail.volume == "12"
    assert detail.pages == "100-115"


@pytest.mark.asyncio
async def test_keying_pdf_url(mock_keying_client):
    """测试科应 PDF URL（mock）"""
    with patch.object(KeyingService, "_get_client", return_value=mock_keying_client):
        url = await KeyingService.get_pdf_url("keying:SR-MOCK-001")
    assert url is not None
    assert "pdforiginal" in url


@pytest.mark.asyncio
async def test_keying_search_with_author(mock_keying_client):
    """测试科应搜索带作者"""
    with patch.object(KeyingService, "_get_client", return_value=mock_keying_client):
        total, results = await KeyingService.search("NLP", author="Alice", page=1, page_size=10)
    # 验证搜索词包含了作者名
    mock_keying_client.search.assert_called_once()
    call_kwargs = mock_keying_client.search.call_args[1]
    assert "Alice" in call_kwargs["query"]


@pytest.mark.asyncio
async def test_keying_detail_not_found(mock_keying_client):
    """测试科应详情不存在"""
    mock_keying_client.get_basic_info.return_value = None
    with patch.object(KeyingService, "_get_client", return_value=mock_keying_client):
        detail = await KeyingService.get_detail("keying:NOT-EXIST")
    assert detail is None


# ---- CLI 管理器测试 ----

def test_cli_registry_register_and_get():
    """测试 CLI 注册表注册和获取"""
    registry = CLIServiceRegistry()
    mock_adapter = MagicMock()
    mock_adapter.source_name = "test_cli"
    registry.register(mock_adapter)
    assert registry.get("test_cli") is mock_adapter
    assert registry.get("not_exist") is None
    assert "test_cli" in registry.sources


def test_cli_registry_list_sources():
    """测试 CLI 注册表列出数据源"""
    registry = CLIServiceRegistry()
    mock1 = MagicMock()
    mock1.source_name = "cli_a"
    mock2 = MagicMock()
    mock2.source_name = "cli_b"
    registry.register(mock1)
    registry.register(mock2)
    sources = registry.list_sources()
    assert len(sources) == 2
    ids = [s["id"] for s in sources]
    assert "cli_a" in ids
    assert "cli_b" in ids


# ---- 搜索聚合服务测试 ----

@pytest.fixture(autouse=True)
def _disable_search_mock_mode():
    """禁用 SEARCH_MOCK_MODE，避免搜索聚合测试走 DB 查询路径。"""
    from app.config import settings
    old_val = settings.SEARCH_MOCK_MODE
    settings.SEARCH_MOCK_MODE = False
    yield
    settings.SEARCH_MOCK_MODE = old_val


@pytest.mark.asyncio
async def test_search_service_aggregate():
    """测试搜索聚合服务（仅 cnki，不依赖外部 API）"""
    result = await SearchService.search(
        query="深度学习",
        sources=["cnki"],
        page=1,
        page_size=20
    )
    assert result["query"] == "深度学习"
    assert "cnki" in result["sources"]
    assert "results" in result
    assert "source_stats" in result


@pytest.mark.asyncio
async def test_search_service_detail():
    """测试聚合服务获取详情"""
    detail = await SearchService.get_detail("cnki:CNKI-12345")
    assert detail is not None
    assert detail.source == "cnki"


@pytest.mark.asyncio
async def test_search_service_pdf_url():
    """测试聚合服务 PDF URL（cnki）"""
    url = await SearchService.get_pdf_url("cnki:CNKI-12345")
    assert url is not None


@pytest.mark.asyncio
async def test_search_service_available_sources():
    """测试可用数据源列表"""
    sources = SearchService.get_available_sources()
    assert len(sources) == 4
    ids = [s["id"] for s in sources]
    assert "arxiv" in ids
    assert "pubmed" in ids
    assert "cnki" in ids
    assert "keying" in ids


@pytest.mark.asyncio
async def test_search_service_cache():
    """测试搜索缓存"""
    result1 = await SearchService.search(
        query="缓存测试", sources=["cnki"], page=1, page_size=5
    )
    result2 = await SearchService.search(
        query="缓存测试", sources=["cnki"], page=1, page_size=5
    )
    assert result1["query"] == result2["query"]
    assert result1["total"] == result2["total"]


@pytest.mark.asyncio
async def test_search_service_relevance_score():
    """测试相关性评分"""
    result = await SearchService.search(
        query="深度学习", sources=["cnki"], page=1, page_size=10
    )
    for item in result["results"]:
        assert 0.0 <= item["relevance_score"] <= 1.0


@pytest.mark.asyncio
async def test_search_service_empty_sources():
    """测试空数据源"""
    # 传入无效的数据源名称，确保过滤后为空
    result = await SearchService.search(
        query="测试", sources=["invalid_source_xyz"], page=1, page_size=10
    )
    assert result["total"] == 0
    assert result["results"] == []
