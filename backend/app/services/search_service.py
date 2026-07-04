"""
PC2 M2 搜索聚合服务
多源文献搜索聚合、缓存、结果合并与排序、搜索结果持久化

P0-C: 搜索失败降级 — 异常时返回缓存结果或空结果 + 建议，不纯报错
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from app.core.cache import cache, make_cache_key
from app.core.database import AsyncSessionLocal
from app.schemas.paper import PaperSearchResult, PaperDetail
from app.services.arxiv_service import ArxivService
from app.services.pubmed_service import pubmed_service
from app.services.cnki_service import CNKIService
from app.services.keying_service import KeyingService
from app.services.degradation import degradation_service
from app.models.paper import Paper, SearchHistory

logger = logging.getLogger(__name__)

# 数据源映射
SOURCE_MAP = {
    "arxiv": ArxivService,
    "pubmed": pubmed_service,
    "cnki": CNKIService,
    "keying": KeyingService,
}

AVAILABLE_SOURCES = list(SOURCE_MAP.keys())


class SearchService:
    """搜索聚合服务"""

    @classmethod
    async def search(
        cls,
        query: str,
        sources: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        journal: Optional[str] = None,
        doi: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """多源聚合搜索"""
        sources = sources or AVAILABLE_SOURCES
        # 过滤有效数据源
        sources = [s for s in sources if s in SOURCE_MAP]

        if not sources:
            return {
                "query": query,
                "sources": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "results": [],
            }

        # 尝试从缓存获取
        cache_key = make_cache_key(
            "search",
            query,
            ",".join(sorted(sources)),
            str(page),
            str(page_size),
            author or "",
            journal or "",
            doi or "",
            str(year_from or ""),
            str(year_to or ""),
        )
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 并行查询各数据源
        tasks = []
        for src in sources:
            service = SOURCE_MAP[src]
            tasks.append(
                cls._safe_search(
                    service, query, page, page_size, author, year_from, year_to
                )
            )

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: List[PaperSearchResult] = []
        total = 0
        source_stats = {}

        all_failed = True
        for src, result in zip(sources, results_list):
            if isinstance(result, Exception):
                source_stats[src] = {"status": "error", "error": str(result), "count": 0}
                continue

            count, items = result
            all_failed = False

            # 客户端过滤（journal / doi）——各源 API 不一定都支持这些过滤
            filtered = items
            if journal:
                filtered = [i for i in filtered if i.journal and journal.lower() in i.journal.lower()]
            if doi:
                filtered = [i for i in filtered if i.doi and doi.lower() == i.doi.lower()]

            total += count
            source_stats[src] = {"status": "ok", "count": count, "filtered": len(filtered)}

            # 添加相关性评分
            for item in filtered:
                item.relevance_score = cls._calc_relevance(item, query)
            all_results.extend(filtered)

        # P0-C: 所有源都失败 → 降级返回
        if all_failed:
            degraded = await degradation_service.search_degraded(query, cache_data=cached)
            degraded.data["sources"] = sources
            degraded.data["source_stats"] = source_stats
            degraded.data["page"] = page
            degraded.data["page_size"] = page_size
            return {**degraded.data, "warnings": degraded.warnings, "degraded": True}

        # 按相关性排序
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paged_results = all_results[start:end]

        response = {
            "query": query,
            "sources": sources,
            "source_stats": source_stats,
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": [r.model_dump() for r in paged_results],
        }

        # 写入缓存
        await cache.set(cache_key, response, ttl=300)

        # 异步写库（搜索结果 + 搜索历史）
        asyncio.create_task(cls._persist_search(query, sources, page, page_size, total, paged_results, user_id))

        return response

    @classmethod
    async def _safe_search(
        cls,
        service,
        query: str,
        page: int,
        page_size: int,
        author: Optional[str],
        year_from: Optional[int],
        year_to: Optional[int],
    ):
        """安全搜索，捕获异常。单源 API 失败时尝试局部降级。

        P2-10: 首先尝试正常搜索；如果失败，记录警告并以空结果兜底，
        而非整个请求失败。
        """
        try:
            return await service.search(query, page, page_size, author, year_from, year_to)
        except Exception as e:
            source_name = getattr(service, "SOURCE", "unknown")
            logger.warning(
                "Source '%s' search failed: %s. Falling back to empty result.",
                source_name, e,
            )
            # P2-10: 单源失败返回空结果，不影响聚合
            return (0, [])

    @classmethod
    def _calc_relevance(cls, paper: PaperSearchResult, query: str) -> float:
        """计算相关性分数（0-1）"""
        score = 0.0
        q = query.lower()

        # 标题匹配权重最高
        if q in paper.title.lower():
            score += 0.5

        # 摘要匹配
        if paper.abstract and q in paper.abstract.lower():
            score += 0.3

        # 关键词匹配
        keywords = getattr(paper, "keywords", None)
        if keywords and any(q in k.lower() for k in keywords):
            score += 0.2

        # 引用量加分
        if paper.citation_count:
            score += min(paper.citation_count / 1000, 0.1)

        # 年份加分（近 3 年）
        if paper.published_at:
            try:
                year = int(str(paper.published_at)[:4])
                if year >= 2024:
                    score += 0.05
            except (ValueError, TypeError):
                pass

        return min(score, 1.0)

    @classmethod
    async def _persist_search(
        cls,
        query: str,
        sources: List[str],
        page: int,
        page_size: int,
        total: int,
        results: List[PaperSearchResult],
        user_id: Optional[str] = None,
    ) -> None:
        """持久化搜索结果到数据库"""
        try:
            from uuid import UUID, uuid5
            from datetime import date

            _PAPER_NS = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

            user_uuid = UUID(user_id) if user_id else None

            async with AsyncSessionLocal() as session:
                # 1. 写搜索历史
                history = SearchHistory(
                    query=query,
                    source=",".join(sources),
                    page=page,
                    page_size=page_size,
                    total_results=total,
                    user_id=user_uuid,
                )
                session.add(history)

                # 2. 写文献记录（upsert：存在则更新，不存在则插入）
                for result in results:
                    paper_uuid = uuid5(_PAPER_NS, f"sciagent:{result.id}")

                    existing = await session.execute(
                        select(Paper).where(Paper.id == paper_uuid)
                    )
                    paper = existing.scalar_one_or_none()
                    if paper:
                        # 更新已有记录 — 只更新有内容的字段
                        if result.title:
                            paper.title = result.title
                        paper.authors = result.authors
                        if result.abstract:
                            paper.abstract = result.abstract
                        paper.search_source = result.source
                        if result.published_at:
                            paper.publication_date = result.published_at if isinstance(result.published_at, date) else date.fromisoformat(str(result.published_at)[:10])
                        paper.doi = result.doi
                        paper.citation_count = result.citation_count or 0
                        paper.relevance_score = result.relevance_score
                        paper.keywords = result.keywords or []
                        paper.openalex_id = result.id
                    else:
                        # 插入新记录
                        pub_date = None
                        if result.published_at:
                            pub_date = result.published_at if isinstance(result.published_at, date) else date.fromisoformat(str(result.published_at)[:10])
                        paper = Paper(
                            id=paper_uuid,
                            title=result.title,
                            authors=result.authors,
                            abstract=result.abstract,
                            search_source=result.source,
                            publication_date=pub_date,
                            doi=result.doi,
                            citation_count=result.citation_count or 0,
                            relevance_score=result.relevance_score,
                            keywords=result.keywords or [],
                            openalex_id=result.id,
                            source_db="openalex",
                        )
                        session.add(paper)

                await session.commit()
        except Exception:
            # 写库失败不影响主流程
            pass

    @classmethod
    async def get_detail(cls, paper_id: str) -> Optional[PaperDetail]:
        """获取文献详情"""
        # 尝试缓存
        cache_key = make_cache_key("detail", paper_id)
        cached = await cache.get(cache_key)
        if cached:
            return PaperDetail(**cached)

        # 解析数据源
        if ":" not in paper_id:
            return None

        source = paper_id.split(":")[0]
        if source not in SOURCE_MAP:
            return None

        service = SOURCE_MAP[source]
        try:
            detail = await service.get_detail(paper_id)
            if detail:
                await cache.set(cache_key, detail.model_dump(), ttl=600)
                # 同时更新数据库
                asyncio.create_task(cls._persist_detail(detail))
            return detail
        except Exception:
            return None

    @classmethod
    async def _persist_detail(cls, detail: PaperDetail) -> None:
        """持久化文献详情"""
        try:
            from uuid import UUID, uuid5
            from datetime import date

            _PAPER_NS = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
            paper_uuid = uuid5(_PAPER_NS, f"sciagent:{detail.id}")

            async with AsyncSessionLocal() as session:
                existing = await session.execute(
                    select(Paper).where(Paper.id == paper_uuid)
                )
                paper = existing.scalar_one_or_none()
                pub_date = None
                if detail.published_at:
                    pub_date = detail.published_at if isinstance(detail.published_at, date) else date.fromisoformat(str(detail.published_at)[:10])

                if paper:
                    paper.title = detail.title
                    paper.authors = detail.authors
                    paper.abstract = detail.abstract
                    paper.search_source = detail.source
                    paper.publication_date = pub_date
                    paper.doi = detail.doi
                    paper.citation_count = detail.citation_count or 0
                    paper.relevance_score = detail.relevance_score
                    paper.keywords = detail.keywords or []
                    paper.journal = detail.journal
                    paper.volume = detail.volume
                    paper.issue = detail.issue
                    paper.pages = detail.pages
                    paper.full_text_url = detail.pdf_url
                    paper.references_json = detail.references or []
                    paper.citations_json = detail.citations or []
                    paper.full_text = detail.full_text
                    paper.openalex_id = detail.id
                else:
                    paper = Paper(
                        id=paper_uuid,
                        title=detail.title,
                        authors=detail.authors,
                        abstract=detail.abstract,
                        search_source=detail.source,
                        publication_date=pub_date,
                        doi=detail.doi,
                        citation_count=detail.citation_count or 0,
                        relevance_score=detail.relevance_score,
                        keywords=detail.keywords or [],
                        journal=detail.journal,
                        volume=detail.volume,
                        issue=detail.issue,
                        pages=detail.pages,
                        full_text_url=detail.pdf_url,
                        references_json=detail.references or [],
                        citations_json=detail.citations or [],
                        full_text=detail.full_text,
                        openalex_id=detail.id,
                        source_db="openalex",
                    )
                    session.add(paper)
                await session.commit()
        except Exception:
            pass

    @classmethod
    async def get_pdf_url(cls, paper_id: str) -> Optional[str]:
        """获取 PDF 下载链接"""
        if ":" not in paper_id:
            return None

        source = paper_id.split(":")[0]
        if source not in SOURCE_MAP:
            return None

        service = SOURCE_MAP[source]
        try:
            return await service.get_pdf_url(paper_id)
        except Exception:
            return None

    @classmethod
    def get_available_sources(cls) -> List[Dict[str, str]]:
        """获取可用数据源列表"""
        return [
            {"id": "arxiv", "name": "arXiv", "description": "预印本论文库", "enabled": True},
            {"id": "pubmed", "name": "PubMed", "description": "生物医学文献库", "enabled": True},
            {"id": "cnki", "name": "CNKI", "description": "中国知网（演示数据）", "enabled": True},
            {"id": "keying", "name": "科应", "description": "科应开放平台（keying-cli 真实对接）", "enabled": True},
        ]
