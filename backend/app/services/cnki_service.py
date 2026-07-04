"""
CNKI 文献检索服务

通过 CNKI_MOCK_MODE 环境变量控制：
- "true"（默认）：使用内置 Mock 数据，适用于开发/测试
- "false"：调用真实 CNKI API
"""

import os
import logging
from typing import List, Optional

import httpx

from app.core.config import get_settings
from app.schemas.paper import PaperSearchResult, PaperDetail

_settings = get_settings()
logger = logging.getLogger(__name__)

# ── Mock 数据 ──────────────────────────────────────────

_MOCK_PAPERS = [
    {
        "id": "cnki:CNKI-12345",
        "title": "基于深度学习的自然语言处理研究综述",
        "authors": ["张三", "李四"],
        "abstract": "本文综述了深度学习在自然语言处理领域的最新进展，包括Transformer模型、预训练语言模型等关键技术。",
        "source": "cnki",
        "published_at": "2024-03-15",
        "doi": "10.1234/cnki.2024.001",
        "citation_count": 128,
        "keywords": ["深度学习", "自然语言处理", "Transformer"],
        "journal": "计算机学报",
        "volume": "47",
        "issue": "3",
        "pages": "512-528",
    },
    {
        "id": "cnki:CNKI-67890",
        "title": "大规模语言模型的训练与优化方法",
        "authors": ["王五", "赵六", "孙七"],
        "abstract": "探讨了大规模语言模型在训练过程中的优化策略，包括分布式训练、混合精度训练等技术。",
        "source": "cnki",
        "published_at": "2024-01-20",
        "doi": "10.1234/cnki.2024.002",
        "citation_count": 85,
        "keywords": ["大语言模型", "分布式训练", "优化算法"],
        "journal": "软件学报",
        "volume": "35",
        "issue": "1",
        "pages": "89-105",
    },
    {
        "id": "cnki:CNKI-11111",
        "title": "知识图谱构建技术与应用",
        "authors": ["周八"],
        "abstract": "系统介绍了知识图谱的构建流程、关键技术及其在智能问答、推荐系统等领域的应用。",
        "source": "cnki",
        "published_at": "2023-11-10",
        "doi": "10.1234/cnki.2023.015",
        "citation_count": 256,
        "keywords": ["知识图谱", "信息抽取", "图神经网络"],
        "journal": "中文信息学报",
        "volume": "37",
        "issue": "11",
        "pages": "1-18",
    },
]


class CNKIService:
    """CNKI 文献服务

    通过 CNKI_MOCK_MODE 环境变量控制模式：
    - "true"（默认）：返回 Mock 数据
    - "false"：调用真实 CNKI HTTP API
    """

    SOURCE = "cnki"
    API_BASE = _settings.CNKI_API_BASE

    @classmethod
    def _is_mock_mode(cls) -> bool:
        """检查是否处于 Mock 模式。

        默认返回 True，仅当环境变量显式设为 'false' 时返回 False。
        """
        mock_val = os.getenv("CNKI_MOCK_MODE", "true").strip().lower()
        return mock_val != "false"

    @classmethod
    def _filter_mock(
        cls,
        query: str,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[dict]:
        """在 Mock 数据中按条件过滤。"""
        filtered = []
        q = query.lower()
        for p in _MOCK_PAPERS:
            match = False
            if q in p["title"].lower() or q in p["abstract"].lower():  # type: ignore[attr-defined]
                match = True
            if author and any(author in a for a in p["authors"]):  # type: ignore[attr-defined]
                match = True
            if year_from or year_to:
                year = int(p["published_at"][:4]) if p["published_at"] else 0  # type: ignore[index]
                if year_from and year < year_from:
                    match = False
                if year_to and year > year_to:
                    match = False
            if match:
                filtered.append(p)
        return filtered

    @classmethod
    async def _search_real(
        cls,
        query: str,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> tuple[int, List[dict]]:
        """通过真实 CNKI HTTP API 搜索文献。

        Raises:
            httpx.HTTPError: API 请求失败。
            RuntimeError: 返回格式异常。
        """
        url = f"{cls.API_BASE}/search"
        params = {
            "q": query,
            "page": page,
            "page_size": page_size,
        }
        if author:
            params["author"] = author
        if year_from:
            params["year_from"] = year_from
        if year_to:
            params["year_to"] = year_to

        logger.info("CNKI 真实 API 搜索: %s", params)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise RuntimeError(f"CNKI API 返回格式异常: {type(data)}")

        total = int(data.get("total", 0))
        items = data.get("results", [])
        return total, items

    @classmethod
    async def _get_detail_real(cls, paper_id: str) -> Optional[dict]:
        """通过真实 CNKI HTTP API 获取文献详情。

        Raises:
            httpx.HTTPError: API 请求失败。
        """
        cnki_id = paper_id.replace("cnki:", "")
        url = f"{cls.API_BASE}/detail/{cnki_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    # ── 公共接口 ──────────────────────────────────────

    @classmethod
    async def search(
        cls,
        query: str,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> tuple[int, List[PaperSearchResult]]:
        """搜索 CNKI 文献"""
        if cls._is_mock_mode():
            filtered = cls._filter_mock(query, author, year_from, year_to)
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            page_items = filtered[start:end]
            results = [PaperSearchResult(**item) for item in page_items]
            return total, results

        # 真实模式
        total, raw_items = await cls._search_real(
            query, page, page_size, author, year_from, year_to
        )
        results = [
            PaperSearchResult(
                id=f"cnki:{item.get('id', '')}",
                title=item.get("title", "无标题"),
                authors=item.get("authors", []),
                abstract=item.get("abstract", ""),
                source=cls.SOURCE,
                published_at=item.get("published_at"),
                doi=item.get("doi"),
                citation_count=item.get("citation_count"),
                relevance_score=0.0,
                keywords=item.get("keywords", []),
                journal=item.get("journal"),
            )
            for item in raw_items
        ]
        return total, results

    @classmethod
    async def get_detail(cls, paper_id: str) -> Optional[PaperDetail]:
        """获取 CNKI 文献详情"""
        if cls._is_mock_mode():
            for p in _MOCK_PAPERS:
                if p["id"] == paper_id:
                    return PaperDetail(
                        **p,
                        relevance_score=0.0,
                        pdf_url=f"https://kns.cnki.net/kcms/detail/detail.aspx?filename={paper_id.replace('cnki:', '')}",
                    )
            return None

        # 真实模式
        item = await cls._get_detail_real(paper_id)
        if not item:
            return None

        return PaperDetail(
            id=paper_id,
            title=item.get("title", "无标题"),
            authors=item.get("authors", []),
            abstract=item.get("abstract", ""),
            source=cls.SOURCE,
            published_at=item.get("published_at"),
            doi=item.get("doi"),
            citation_count=item.get("citation_count"),
            relevance_score=0.0,
            keywords=item.get("keywords", []),
            journal=item.get("journal"),
            volume=item.get("volume"),
            issue=item.get("issue"),
            pages=item.get("pages"),
            pdf_url=item.get("pdf_url"),
        )

    @classmethod
    async def get_pdf_url(cls, paper_id: str) -> Optional[str]:
        """获取 PDF 链接"""
        if cls._is_mock_mode():
            for p in _MOCK_PAPERS:
                if p["id"] == paper_id:
                    return f"https://kns.cnki.net/kcms/detail/detail.aspx?filename={paper_id.replace('cnki:', '')}"
            return None

        # 真实模式
        cnki_id = paper_id.replace("cnki:", "")
        url = f"{cls.API_BASE}/pdf/{cnki_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("pdf_url")  # type: ignore[no-any-return]
