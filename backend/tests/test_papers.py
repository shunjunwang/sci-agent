"""
PC2 M2 文献检索 API 测试
科应相关测试使用 mock，避免依赖真实 API

P4-07: 修复认证头缺失问题。使用 auth_client fixture 替代 client。
需要外部 API（CNKI）的测试单独标记 skip。
"""

import pytest

from unittest.mock import patch, MagicMock


# ---- 搜索 API 测试 ----

@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_search_papers_cnki_only(auth_client):
    """测试文献搜索 - 仅 CNKI 数据源"""
    response = await auth_client.get("/api/v2/papers/search?q=深度学习&source=cnki")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["query"] == "深度学习"
    assert "results" in data["data"]
    assert "total" in data["data"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_search_papers_all_sources(auth_client):
    """测试文献搜索 - 所有数据源"""
    # 仅用 cnki 避免外部 API 依赖
    response = await auth_client.get("/api/v2/papers/search?q=machine+learning&page=1&page_size=10&source=cnki")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 10


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_search_papers_with_filters(auth_client):
    """测试高级检索过滤"""
    response = await auth_client.get(
        "/api/v2/papers/search?q=自然语言处理&author=张三&year_from=2023&year_to=2024&source=cnki"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_search_papers_with_journal_filter(auth_client):
    """测试期刊过滤"""
    response = await auth_client.get(
        "/api/v2/papers/search?q=深度学习&journal=计算机学报&source=cnki"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200


@pytest.mark.asyncio
async def test_search_papers_no_query(auth_client):
    """测试缺少关键词参数（422 校验，无需外部 API）"""
    response = await auth_client.get("/api/v2/papers/search")
    assert response.status_code == 422


# ---- 科应 API 测试（Mock keying-cli） ----

MOCK_SEARCH_DATA = [
    {
        "srid": "SR-MOCK-001",
        "originalTitle": "Deep Learning",
        "chineseTitle": "深度学习",
        "originalAuthors": ["Alice"],
        "chineseAbstract": "摘要内容",
        "publicationDate": "2024-01-01",
        "doi": "10.1234/mock",
        "dataSource": "Nature",
        "featuredTags": [],
        "hasPdf": True,
        "docType": "papers",
    }
]

MOCK_DETAIL_DATA = {
    "srid": "SR-MOCK-001",
    "originalTitle": "Deep Learning",
    "chineseTitle": "深度学习",
    "originalAuthors": ["Alice"],
    "chineseAbstract": "摘要内容",
    "publicationDate": "2024-01-01",
    "doi": "10.1234/mock",
    "dataSource": "Nature",
    "featuredTags": [],
    "hasPdf": True,
    "docType": "papers",
    "refIds": [],
}


@pytest.fixture
def mock_keying():
    """Mock keying-cli"""
    mock_client = MagicMock()
    mock_client.search.return_value = (MOCK_SEARCH_DATA, 100)
    mock_client.get_basic_info.return_value = MOCK_DETAIL_DATA
    mock_client.get_pdf_url.return_value = "https://picture-m.scienceing.com/pdforiginal/mock.pdf"
    return mock_client


@pytest.mark.asyncio
async def test_search_papers_keying_mock(auth_client, mock_keying):
    """测试科应搜索（mock）"""
    from app.config import settings
    old_val = settings.SEARCH_MOCK_MODE
    settings.SEARCH_MOCK_MODE = False
    try:
        with patch("app.services.keying_service.KeyingService._get_client", return_value=mock_keying):
            response = await auth_client.get("/api/v2/papers/search?q=深度学习&sources=keying")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 100
    finally:
        settings.SEARCH_MOCK_MODE = old_val


@pytest.mark.asyncio
async def test_get_paper_detail_keying_mock(auth_client, mock_keying):
    """测试获取科应文献详情（mock）"""
    with patch("app.services.keying_service.KeyingService._get_client", return_value=mock_keying):
        response = await auth_client.get("/api/v2/papers/keying:SR-MOCK-001")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["id"] == "keying:SR-MOCK-001"
    assert data["data"]["journal"] == "Nature"


@pytest.mark.asyncio
async def test_download_pdf_keying_mock(auth_client, mock_keying):
    """测试科应 PDF 下载重定向（mock）"""
    with patch("app.services.keying_service.KeyingService._get_client", return_value=mock_keying):
        response = await auth_client.get("/api/v2/papers/keying:SR-MOCK-001/pdf", follow_redirects=False)
    assert response.status_code == 307
    assert "pdforiginal" in response.headers["location"]


# ---- CNKI API 测试 ----

@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_get_paper_detail_cnki(auth_client):
    """测试获取 CNKI 文献详情"""
    response = await auth_client.get("/api/v2/papers/cnki:CNKI-12345")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["id"] == "cnki:CNKI-12345"
    assert data["data"]["title"] == "基于深度学习的自然语言处理研究综述"


@pytest.mark.asyncio
async def test_get_paper_detail_not_found(auth_client):
    """测试获取不存在的文献"""
    response = await auth_client.get("/api/v2/papers/cnki:NOT-EXIST")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要真实 CNKI API 连接，本地测试环境不可用")
async def test_download_pdf_cnki(auth_client):
    """测试 CNKI PDF 下载重定向"""
    response = await auth_client.get("/api/v2/papers/cnki:CNKI-12345/pdf", follow_redirects=False)
    assert response.status_code == 307
    assert "kns.cnki.net" in response.headers["location"]


@pytest.mark.asyncio
async def test_download_pdf_not_found(auth_client):
    """测试下载不存在的 PDF"""
    response = await auth_client.get("/api/v2/papers/cnki:NOT-EXIST/pdf")
    assert response.status_code == 404
