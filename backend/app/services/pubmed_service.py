"""
# mypy: disable-error-code="no-untyped-def"
PubMed 文献检索服务
使用 NCBI E-utilities API
"""

import re
import logging
from datetime import date
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

# 重试参数
_RETRY_ATTEMPTS = 3
_RETRY_MIN_WAIT = 1
_RETRY_MAX_WAIT = 10


def _is_retryable(exc: BaseException) -> bool:
    """判断异常是否可重试：仅对 5xx 和 TimeoutException 重试。"""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600
    return False


# PubMed 重试装饰器
_pubmed_retry = retry(
    stop=stop_after_attempt(_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=_RETRY_MIN_WAIT, max=_RETRY_MAX_WAIT),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    retry_error_callback=lambda retry_state: _handle_retry_failure(retry_state),
    before_sleep=lambda retry_state: logger.warning(
        "PubMed API 调用失败（第 %d/%d 次），%s 后重试...",
        retry_state.attempt_number,
        _RETRY_ATTEMPTS,
        f"{retry_state.next_action.sleep:.0f}s" if retry_state.next_action else "即将",
    ),
)


def _handle_retry_failure(retry_state):
    """重试全部失败后的回调：重新抛出原始异常。"""
    exc = retry_state.outcome.exception()
    raise exc


def _parse_pubdate(pubdate: str):
    """解析 PubMed pubdate 字符串为 date 对象。"""
    if not pubdate:
        return None
    parts = pubdate.split()
    if parts:
        year_str = parts[0]
        year_str = year_str[:4] if len(year_str) >= 4 else year_str
        try:
            year_int = int(year_str)
            return date(year_int, 1, 1)
        except (ValueError, TypeError):
            return None
    return None


def _safe_citation_count(raw) -> Optional[int]:
    """安全转换引用数为 int。"""
    if raw in (None, "", "N/A"):
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def _extract_abstract(xml_text: str) -> tuple[str, list[str]]:
    """从 PubMed XML 中提取摘要文本，返回 (abstract, parse_warnings)。"""
    if "<Abstract>" not in xml_text:
        return "", []

    warnings: list[str] = []
    try:
        start = xml_text.find("<AbstractText>")
        if start == -1:
            start = xml_text.find("<Abstract>")
        end = xml_text.find("</Abstract>")
        if start != -1 and end != -1:
            abstract = xml_text[start:end]
            abstract = re.sub(r"<[^>]+>", "", abstract)
            return abstract, warnings
    except Exception as e:
        warnings.append(f"摘要解析失败: {e}")

    return "", warnings


class PubmedService:
    """PubMed 文献服务"""

    SOURCE = "pubmed"
    API_BASE = _settings.PUBMED_API_BASE

    def __init__(self):
        """创建类级别的 httpx AsyncClient 单例，复用连接池。"""
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 AsyncClient 单例。"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """关闭 AsyncClient，释放连接。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> tuple[int, List[PaperSearchResult]]:
        """搜索 PubMed 文献"""
        # 构建搜索词
        search_term = query
        if author:
            search_term = f"{author}[Author] AND {search_term}"
        if year_from or year_to:
            yf = year_from or 1800
            yt = year_to or 3000
            search_term = f"{search_term} AND ({yf}[PDAT] : {yt}[PDAT])"

        # Step 1: esearch 获取 ID 列表
        esearch_url = (
            f"{self.API_BASE}/esearch.fcgi"
            f"?db=pubmed&term={search_term}"
            f"&retstart={(page - 1) * page_size}"
            f"&retmax={page_size}"
            f"&retmode=json"
        )

        client = await self._get_client()

        @_pubmed_retry
        async def _esearch():
            resp = await client.get(esearch_url)
            resp.raise_for_status()
            return resp.json()

        data = await _esearch()
        idlist = data.get("esearchresult", {}).get("idlist", [])
        total = int(data.get("esearchresult", {}).get("count", 0))

        if not idlist:
            return total, []

        # Step 2: esummary 获取摘要信息
        esummary_url = (
            f"{self.API_BASE}/esummary.fcgi"
            f"?db=pubmed&id={','.join(idlist)}"
            f"&retmode=json"
        )

        @_pubmed_retry
        async def _esummary():
            resp = await client.get(esummary_url)
            resp.raise_for_status()
            return resp.json()

        summary_data = await _esummary()

        results = []
        result_dict = summary_data.get("result", {})
        for uid in idlist:
            item = result_dict.get(uid, {})
            if not item:
                continue

            title = item.get("title", "无标题")
            authors_list = []
            for au in item.get("authors", []):
                name = au.get("name")
                if name:
                    authors_list.append(name)

            published_at = _parse_pubdate(item.get("pubdate", ""))

            doi = None
            for articleid in item.get("articleids", []):
                if articleid.get("idtype") == "doi":
                    doi = articleid.get("value")
                    break

            citation_count = _safe_citation_count(item.get("pmcrefcount"))

            results.append(
                PaperSearchResult(
                    id=f"pubmed:{uid}",
                    title=title,
                    authors=authors_list,
                    abstract="",  # esummary 不返回摘要，需要用 efetch
                    source=self.SOURCE,
                    published_at=published_at,
                    doi=doi,
                    citation_count=citation_count,
                    relevance_score=0.0,
                )
            )

        return total, results

    async def get_detail(self, paper_id: str) -> Optional[PaperDetail]:
        """获取 PubMed 文献详情"""
        uid = paper_id.replace("pubmed:", "")
        parse_warnings: list[str] = []

        client = await self._get_client()

        # 获取摘要和详细信息
        efetch_url = (
            f"{self.API_BASE}/efetch.fcgi"
            f"?db=pubmed&id={uid}&rettype=abstract"
        )

        @_pubmed_retry
        async def _efetch():
            resp = await client.get(efetch_url)
            resp.raise_for_status()
            return resp.text

        xml_text = await _efetch()

        # 同时也用 esummary 获取结构化信息
        esummary_url = (
            f"{self.API_BASE}/esummary.fcgi"
            f"?db=pubmed&id={uid}&retmode=json"
        )

        @_pubmed_retry
        async def _esummary():
            resp = await client.get(esummary_url)
            resp.raise_for_status()
            return resp.json()

        data = await _esummary()

        item = data.get("result", {}).get(uid, {})
        if not item:
            return None

        title = item.get("title", "无标题")
        authors_list = []
        for au in item.get("authors", []):
            name = au.get("name")
            if name:
                authors_list.append(name)

        published_at = _parse_pubdate(item.get("pubdate", ""))

        doi = None
        for articleid in item.get("articleids", []):
            if articleid.get("idtype") == "doi":
                doi = articleid.get("value")
                break

        # 从 XML 中提取摘要（结构化错误处理）
        abstract, xml_warnings = _extract_abstract(xml_text)
        parse_warnings.extend(xml_warnings)

        # 期刊名
        journal = item.get("fulljournalname") or item.get("source", "")

        # 构建 PDF URL（PMC 开放获取）
        pmcid = None
        for articleid in item.get("articleids", []):
            if articleid.get("idtype") == "pmc":
                pmcid = articleid.get("value")
                break

        pdf_url = None
        if pmcid:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"

        citation_count = _safe_citation_count(item.get("pmcrefcount"))

        # 构建详情，附加 parse_warnings 到 metadata
        detail = PaperDetail(
            id=paper_id,
            title=title,
            authors=authors_list,
            abstract=abstract,
            source=self.SOURCE,
            published_at=published_at,
            doi=doi,
            citation_count=citation_count,
            relevance_score=0.0,
            keywords=item.get("meshterms", []),
            journal=journal,
            pdf_url=pdf_url,
        )

        if parse_warnings:
            logger.warning(
                "PubMed 文献 %s 解析警告: %s",
                paper_id,
                "; ".join(parse_warnings),
            )

        return detail

    async def get_pdf_url(self, paper_id: str) -> Optional[str]:
        """获取 PDF 直链（如果可用）"""
        uid = paper_id.replace("pubmed:", "")

        esummary_url = (
            f"{self.API_BASE}/esummary.fcgi"
            f"?db=pubmed&id={uid}&retmode=json"
        )

        client = await self._get_client()

        @_pubmed_retry
        async def _esummary():
            resp = await client.get(esummary_url)
            resp.raise_for_status()
            return resp.json()

        data = await _esummary()
        item = data.get("result", {}).get(uid, {})
        for articleid in item.get("articleids", []):
            if articleid.get("idtype") == "pmc":
                pmcid = articleid.get("value")
                return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        return None


# 全局单例（替代原来的类方法模式）
pubmed_service = PubmedService()
