"""
# mypy: disable-error-code="no-untyped-def"
科应文献检索服务 - 基于 keying-cli 真实对接
通过 CLISearchAdapter 协议实现，可被通用 CLI 管理器注册
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.exceptions import KeyingServiceError
from app.schemas.paper import PaperSearchResult, PaperDetail

logger = logging.getLogger(__name__)

# 科应客户端调用超时（秒）
_KEYING_TIMEOUT = 30
# 重试参数
_RETRY_ATTEMPTS = 3
_RETRY_MIN_WAIT = 1
_RETRY_MAX_WAIT = 10


class KeyingService:
    """科应文献服务 - 封装 keying-cli"""

    SOURCE = "keying"
    source_name = "keying"  # CLISearchAdapter 协议字段

    @classmethod
    def _get_client(cls):
        """延迟导入 keying_cli，避免未安装时影响启动"""
        from keying_cli import ScienceRiverClient
        return ScienceRiverClient()

    @classmethod
    def _ensure_env(cls):
        """确保环境变量已设置（keying-cli 通过环境变量认证）"""
        # keying-cli 通过 SCIENCERIVER_APP_ID / SCIENCERIVER_APP_SECRET 环境变量认证
        # 这些在 main.py 启动时从 .env 加载并设置到 os.environ
        pass

    @classmethod
    def _raw_to_search_result(cls, raw: Dict[str, Any]) -> PaperSearchResult:
        """将科应 API 原始数据转换为统一搜索结果模型"""
        srid = raw.get("srid", "")
        title = raw.get("chineseTitle") or raw.get("originalTitle") or "无标题"
        authors = raw.get("originalAuthors") or []
        abstract = raw.get("chineseAbstract") or raw.get("originalAbstract") or ""
        pub_date = raw.get("publicationDate")
        doi = raw.get("doi")
        featured_tags = raw.get("featuredTags") or []

        return PaperSearchResult(
            id=f"keying:{srid}",
            title=title,
            authors=authors,
            abstract=abstract or "",
            source=cls.SOURCE,
            published_at=pub_date,
            doi=doi,
            citation_count=None,
            relevance_score=0.0,
            keywords=featured_tags,
        )

    @classmethod
    def _raw_to_detail(cls, raw: Dict[str, Any], pdf_url: Optional[str] = None) -> PaperDetail:
        """将科应 API 原始数据转换为统一详情模型"""
        srid = raw.get("srid", "")
        title = raw.get("chineseTitle") or raw.get("originalTitle") or "无标题"
        authors = raw.get("originalAuthors") or []
        abstract = raw.get("chineseAbstract") or raw.get("originalAbstract") or ""
        pub_date = raw.get("publicationDate")
        doi = raw.get("doi")
        featured_tags = raw.get("featuredTags") or []
        data_source = raw.get("dataSource")
        volume = raw.get("volume")
        issue = raw.get("issue")
        start_page = raw.get("startPage")
        end_page = raw.get("endPage")

        pages = None
        if start_page and end_page:
            pages = f"{start_page}-{end_page}"
        elif start_page:
            pages = str(start_page)

        return PaperDetail(
            id=f"keying:{srid}",
            title=title,
            authors=authors,
            abstract=abstract or "",
            source=cls.SOURCE,
            published_at=pub_date,
            doi=doi,
            citation_count=None,
            relevance_score=0.0,
            keywords=featured_tags,
            journal=data_source,
            volume=str(volume) if volume else None,
            issue=str(issue) if issue else None,
            pages=pages,
            pdf_url=pdf_url,
            references=raw.get("refIds") or [],
        )

    @classmethod
    def _retry_decorator(cls):
        """构建 tenacity 重试装饰器（仅对网络错误重试，含指数退避）。

        Returns:
            retry 装饰器，失败时抛 KeyingServiceError。
        """
        return retry(
            stop=stop_after_attempt(_RETRY_ATTEMPTS),
            wait=wait_exponential(
                multiplier=1, min=_RETRY_MIN_WAIT, max=_RETRY_MAX_WAIT
            ),
            retry=retry_if_exception_type(
                (asyncio.TimeoutError, OSError, ConnectionError, TimeoutError)
            ),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                "科应 API 调用失败（第 %d/%d 次），%s 后重试...",
                retry_state.attempt_number,
                _RETRY_ATTEMPTS,
                f"{retry_state.next_action.sleep:.0f}s" if retry_state.next_action else "即将",
            ),
        )

    @classmethod
    async def _run_with_timeout(cls, coro):
        """带超时的异步执行包装器。

        Args:
            coro: 要执行的协程。

        Returns:
            协程结果。

        Raises:
            KeyingServiceError: 超时或执行失败。
        """
        try:
            return await asyncio.wait_for(coro, timeout=_KEYING_TIMEOUT)
        except asyncio.TimeoutError:
            raise KeyingServiceError(
                f"科应服务调用超时（>{_KEYING_TIMEOUT}s），请稍后重试"
            )

    @classmethod
    async def search(
        cls,
        query: str,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        **kwargs,
    ) -> tuple[int, List[PaperSearchResult]]:
        """搜索科应文献"""
        cls._ensure_env()
        client = cls._get_client()

        search_query = query
        if author:
            search_query = f"{author} {query}"

        @cls._retry_decorator()
        async def _do_search():
            loop = asyncio.get_event_loop()
            return await cls._run_with_timeout(
                loop.run_in_executor(
                    None,
                    lambda: client.search(
                        query=search_query,
                        scope="papers",
                        page=page,
                        per_page=page_size,
                        date_from=str(year_from) if year_from else None,
                        date_to=str(year_to) if year_to else None,
                    ),
                )
            )

        try:
            results_raw, total = await _do_search()
        except KeyingServiceError:
            raise
        except Exception as e:
            raise KeyingServiceError(
                f"科应服务暂时不可用: {e}"
            ) from e

        results = [cls._raw_to_search_result(r) for r in results_raw]
        return total, results

    @classmethod
    async def get_detail(cls, paper_id: str) -> Optional[PaperDetail]:
        """获取科应文献详情"""
        cls._ensure_env()

        srid = paper_id.replace("keying:", "")
        if not srid:
            return None

        client = cls._get_client()

        @cls._retry_decorator()
        async def _do_get_info():
            loop = asyncio.get_event_loop()
            return await cls._run_with_timeout(
                loop.run_in_executor(
                    None, lambda: client.get_basic_info(srid=srid)
                )
            )

        try:
            info = await _do_get_info()
        except KeyingServiceError:
            raise
        except Exception as e:
            raise KeyingServiceError(
                f"科应服务暂时不可用: {e}"
            ) from e

        if not info:
            return None

        # 获取 PDF URL（非关键路径，失败不抛异常）
        pdf_url = None
        try:
            if info.get("hasPdf"):
                pdf_url = await cls._run_with_timeout(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: client.get_pdf_url(srid=srid)
                    )
                )
        except Exception:
            logger.warning("获取科应文献 PDF URL 失败: srid=%s", srid)

        return cls._raw_to_detail(info, pdf_url)

    @classmethod
    async def get_pdf_url(cls, paper_id: str) -> Optional[str]:
        """获取 PDF 链接"""
        cls._ensure_env()
        srid = paper_id.replace("keying:", "")
        if not srid:
            return None

        client = cls._get_client()

        @cls._retry_decorator()
        async def _do_get_pdf():
            loop = asyncio.get_event_loop()
            return await cls._run_with_timeout(
                loop.run_in_executor(
                    None, lambda: client.get_pdf_url(srid=srid)
                )
            )

        try:
            return await _do_get_pdf()  # type: ignore[no-any-return]
        except KeyingServiceError:
            raise
        except Exception as e:
            raise KeyingServiceError(
                f"科应服务暂时不可用: {e}"
            ) from e
