"""
arXiv 文献检索服务
使用 arXiv API: https://export.arxiv.org/api/query
"""

import xml.etree.ElementTree as ET
import logging
from typing import List, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import get_settings
from app.schemas.paper import PaperSearchResult, PaperDetail

_settings = get_settings()
logger = logging.getLogger(__name__)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# 重试参数
_RETRY_ATTEMPTS = 3
_RETRY_MIN_WAIT = 1
_RETRY_MAX_WAIT = 10


def _is_retryable(exc: BaseException) -> bool:
    """判断异常是否可重试：仅对 5xx 和 TimeoutException 重试，4xx 不重试。"""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600
    return False


# 统一的 arXiv 重试装饰器
_arxiv_retry = retry(
    stop=stop_after_attempt(_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=_RETRY_MIN_WAIT, max=_RETRY_MAX_WAIT),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    retry_error_callback=lambda retry_state: _handle_retry_failure(retry_state),
    before_sleep=lambda retry_state: logger.warning(
        "arXiv API 调用失败（第 %d/%d 次），状态码: %s，%s 后重试...",
        retry_state.attempt_number,
        _RETRY_ATTEMPTS,
        _get_status_code(retry_state.outcome.exception()) if retry_state.outcome else "未知",
        f"{retry_state.next_action.sleep:.0f}s" if retry_state.next_action else "即将",
    ),
)


def _get_status_code(exc: BaseException) -> str:
    """从异常中提取 HTTP 状态码描述。"""
    if isinstance(exc, httpx.HTTPStatusError):
        return str(exc.response.status_code)
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    return type(exc).__name__


def _handle_retry_failure(retry_state):
    """重试全部失败后的回调：重新抛出原始异常。"""
    exc = retry_state.outcome.exception()
    if isinstance(exc, httpx.HTTPStatusError):
        # 如果是 4xx，说明业务层错误，直接传播
        # 如果是 5xx 全部重试仍失败，也直接传播
        raise exc
    raise exc


class ArxivService:
    """arXiv 文献服务"""

    SOURCE = "arxiv"
    API_BASE = _settings.ARXIV_API_BASE

    @staticmethod
    def _extract_id(entry_id: str) -> str:
        """从 arXiv URL 中提取 ID"""
        # http://arxiv.org/abs/2401.12345 -> arxiv:2401.12345
        if "/abs/" in entry_id:
            return f"arxiv:{entry_id.split('/abs/')[-1]}"
        return f"arxiv:{entry_id}"

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
        """搜索 arXiv 文献"""
        start = (page - 1) * page_size

        # 构建搜索查询
        search_query = f"all:{query}"
        if author:
            search_query = f"au:{author}+AND+{search_query}"
        if year_from:
            search_query = f"{search_query}+AND+submittedDate:[{year_from}0101+TO+{year_to or 9999}1231]"

        url = (
            f"{cls.API_BASE}"
            f"?search_query={search_query}"
            f"&start={start}&max_results={page_size}"
            f"&sortBy=relevance&sortOrder=descending"
        )

        @_arxiv_retry
        async def _fetch():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text

        xml_text = await _fetch()
        root = ET.fromstring(xml_text)

        total = 0
        total_results = root.find(
            "opensearch:totalResults",
            {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"},
        )
        if total_results is not None and total_results.text:
            total = int(total_results.text)

        results: List[PaperSearchResult] = []
        for entry in root.findall("atom:entry", NS):
            entry_id = entry.find("atom:id", NS)
            title = entry.find("atom:title", NS)
            summary = entry.find("atom:summary", NS)
            published = entry.find("atom:published", NS)

            authors = []
            for author_elem in entry.findall("atom:author", NS):
                name = author_elem.find("atom:name", NS)
                if name is not None and name.text:
                    authors.append(name.text)

            doi_elem = entry.find("arxiv:doi", NS)
            doi = doi_elem.text if doi_elem is not None else None

            paper_id = (
                cls._extract_id(entry_id.text)
                if entry_id is not None and entry_id.text
                else ""
            )
            pub_date = (
                published.text[:10]
                if published is not None and published.text
                else None
            )

            results.append(
                PaperSearchResult(
                    id=paper_id,
                    title=title.text.strip()
                    if title is not None and title.text
                    else "无标题",
                    authors=authors,
                    abstract=summary.text.strip()
                    if summary is not None and summary.text
                    else "",
                    source=cls.SOURCE,
                    published_at=pub_date,
                    doi=doi,
                    citation_count=None,
                    relevance_score=0.0,
                )
            )

        return total, results

    @classmethod
    async def get_detail(cls, paper_id: str) -> Optional[PaperDetail]:
        """获取 arXiv 文献详情"""
        arxiv_id = paper_id.replace("arxiv:", "")
        url = f"{cls.API_BASE}?id_list={arxiv_id}"

        @_arxiv_retry
        async def _fetch():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text

        xml_text = await _fetch()
        root = ET.fromstring(xml_text)

        entry = root.find("atom:entry", NS)
        if entry is None:
            return None

        entry_id = entry.find("atom:id", NS)
        title = entry.find("atom:title", NS)
        summary = entry.find("atom:summary", NS)
        published = entry.find("atom:published", NS)

        authors = []
        for author_elem in entry.findall("atom:author", NS):
            name = author_elem.find("atom:name", NS)
            if name is not None and name.text:
                authors.append(name.text)

        doi_elem = entry.find("arxiv:doi", NS)
        doi = doi_elem.text if doi_elem is not None else None

        # PDF 链接
        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break

        # 分类作为关键词
        categories = []
        for cat in entry.findall("atom:category", NS):
            term = cat.get("term")
            if term:
                categories.append(term)

        return PaperDetail(
            id=cls._extract_id(entry_id.text)
            if entry_id is not None and entry_id.text
            else paper_id,
            title=title.text.strip()
            if title is not None and title.text
            else "无标题",
            authors=authors,
            abstract=summary.text.strip()
            if summary is not None and summary.text
            else "",
            source=cls.SOURCE,
            published_at=published.text[:10]
            if published is not None and published.text
            else None,
            doi=doi,
            citation_count=None,
            relevance_score=0.0,
            keywords=categories,
            journal="arXiv",
            pdf_url=pdf_url,
        )

    @classmethod
    async def get_pdf_url(cls, paper_id: str) -> Optional[str]:
        """获取 PDF 直链"""
        arxiv_id = paper_id.replace("arxiv:", "")
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
