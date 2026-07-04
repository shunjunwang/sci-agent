"""
P0-C: 失败降级服务

五个核心场景的降级策略：
1. 搜索降级 — 返回缓存结果 + 标注时间
2. 沙箱降级 — 返回部分输出 + 建议
3. PDF 解析降级 — 返回 OCR 文本 + 警告
4. 写作超时降级 — 返回已完成部分
5. 哈希链断裂 — 报告断裂点 + 阻止写入

核心原则：宁可有损可用，不可纯报错白屏。
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DegradationResult:
    """降级结果包装器。

    Attributes:
        degraded: 是否为降级结果。
        data: 降级后返回的数据。
        warnings: 降级警告信息列表。
        degraded_at: 降级发生时间。
    """

    def __init__(self, data: Any, warnings: Optional[list] = None) -> None:
        self.degraded = True
        self.data = data
        self.warnings = warnings or []
        self.degraded_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "degraded": self.degraded,
            "data": self.data,
            "warnings": self.warnings,
            "degraded_at": self.degraded_at,
        }


class DegradationService:
    """失败降级服务。

    在各模块关键路径中拦截异常，返回降级结果而非直接抛出错误。
    """

    # ── 1. 搜索降级 ─────────────────────────────────

    @staticmethod
    def search_degraded(
        original_query: str,
        cache_data: Optional[Dict[str, Any]] = None,
    ) -> DegradationResult:
        """搜索服务降级：返回缓存结果 + 标注时间。

        当实时搜索因超时/网络/API错误失败时调用。
        如果有历史缓存，返回缓存并标注时间；无缓存则返回空结果并提示稍后重试。

        Args:
            original_query: 原始搜索查询。
            cache_data: 可选的缓存数据。

        Returns:
            DegradationResult: 降级结果。
        """
        warnings = []

        if cache_data:
            cache_age = cache_data.get("cached_at", "未知")
            warnings.append(
                f"实时搜索暂时不可用，当前展示的是 {cache_age} 的缓存结果，"
                f"数据可能不是最新的。请稍后重试以获取最新文献。"
            )
            logger.warning(
                "Search degraded: using cached results for query=%s, cache_age=%s",
                original_query, cache_age,
            )
            return DegradationResult(
                data=cache_data,
                warnings=warnings,
            )

        warnings.append(
            "搜索服务暂时不可用，请检查网络连接后重试。"
            "建议：尝试缩小搜索范围或切换数据源（arXiv/PubMed/知网）。"
        )
        logger.warning("Search degraded: no cache available for query=%s", original_query)
        return DegradationResult(
            data={
                "query": original_query,
                "sources": [],
                "total": 0,
                "results": [],
                "source_stats": {},
            },
            warnings=warnings,
        )

    # ── 2. 沙箱降级 ─────────────────────────────────

    @staticmethod
    def sandbox_degraded(
        job_uid: str,
        partial_output: Optional[str] = None,
        error_msg: Optional[str] = None,
        language: str = "python",
    ) -> DegradationResult:
        """沙箱执行降级：返回部分输出 + 建议。

        当 Docker 不可用、容器启动失败或超时 kill 时调用。

        Args:
            job_uid: 沙箱任务 UID。
            partial_output: 超时前的部分 stdout。
            error_msg: 原始错误信息。
            language: 执行语言。

        Returns:
            DegradationResult: 降级结果。
        """
        warnings = []

        if partial_output:
            warnings.append(
                f"沙箱执行超时或中断（job_uid={job_uid}），"
                "以下为停止前的部分输出，可能不完整。"
            )
            suggestions = [
                "优化代码，减少数据规模或迭代次数",
                "检查是否陷入死循环",
                f"当前超时限制：300 秒，可考虑分步执行",
            ]
        else:
            warnings.append(
                f"沙箱环境暂时不可用（job_uid={job_uid}）。"
                "可能原因：Docker 服务未运行、镜像缺失或资源不足。"
            )
            suggestions = [
                "确认 Docker 服务已启动",
                "检查镜像 sci-agent/sandbox:latest 是否已拉取",
                "检查系统内存和 CPU 资源",
            ]

        report = {
            "job_uid": job_uid,
            "status": "degraded",
            "partial_output": partial_output,
            "error_hint": error_msg,
            "language": language,
            "suggestions": suggestions,
        }

        logger.warning(
            "Sandbox degraded: job_uid=%s, has_partial=%s",
            job_uid, bool(partial_output),
        )
        return DegradationResult(data=report, warnings=warnings)

    # ── 3. PDF 解析降级 ─────────────────────────────

    @staticmethod
    def pdf_parse_degraded(
        file_name: str,
        raw_text: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> DegradationResult:
        """PDF 解析降级：返回 OCR 文本 + 警告。

        当 PDF 解析失败（损坏/加密/扫描版无OCR）时调用。

        Args:
            file_name: PDF 文件名。
            raw_text: 已提取的部分原始文本。
            error_msg: 原始错误信息。

        Returns:
            DegradationResult: 降级结果。
        """
        warnings = []

        if raw_text:
            warnings.append(
                f"PDF '{file_name}' 解析不完整，以下为部分提取的文本。"
                "可能原因：文件包含扫描图片，建议使用专业 OCR 工具重新识别。"
            )
        else:
            warnings.append(
                f"无法解析 PDF '{file_name}'。可能原因："
                "文件已损坏、加密或为纯扫描版。"
                "建议：使用 Adobe Acrobat / ABBYY 等专业工具转换。"
            )

        report = {
            "file_name": file_name,
            "status": "degraded",
            "partial_text": raw_text,
            "error_hint": error_msg,
            "note": "以上内容为降级解析结果，格式和排版可能丢失，请以原始 PDF 为准。",
        }

        logger.warning(
            "PDF parse degraded: file=%s, has_partial=%s",
            file_name, bool(raw_text),
        )
        return DegradationResult(data=report, warnings=warnings)

    # ── 4. 写作超时降级 ────────────────────────────

    @staticmethod
    def writing_timeout_degraded(
        document_title: str,
        completed_sections: Optional[list] = None,
        current_section: Optional[str] = None,
    ) -> DegradationResult:
        """写作服务降级：返回已完成部分 + 建议继续方式。

        当 LLM 生成超时或长篇内容被截断时调用。

        Args:
            document_title: 文档标题。
            completed_sections: 已完成的章节列表，每项 {"title": ..., "content": ...}。
            current_section: 被中断时正在生成的章节。

        Returns:
            DegradationResult: 降级结果。
        """
        warnings = []
        section_count = len(completed_sections) if completed_sections else 0

        if completed_sections:
            warnings.append(
                f"文档「{document_title}」生成超时，已完成 {section_count} 个章节。"
                f"当前中断于「{current_section or '未知章节'}」。"
                "建议：使用「从断点续写」功能继续，或减小单次请求的章节长度。"
            )
        else:
            warnings.append(
                f"文档「{document_title}」生成失败——未完成任何章节。"
                "建议：缩小主题范围、减少要求文献数量后重试。"
            )

        report = {
            "document_title": document_title,
            "status": "degraded",
            "completed_sections": completed_sections or [],
            "interrupted_section": current_section,
            "completed_count": section_count,
            "can_resume": section_count > 0,
            "resume_hint": (
                f"从「{current_section or '下一章节'}」继续生成" if section_count > 0
                else None
            ),
        }

        logger.warning(
            "Writing degraded: title=%s, completed=%d, interrupted=%s",
            document_title, section_count, current_section,
        )
        return DegradationResult(data=report, warnings=warnings)

    # ── 5. 哈希链断裂 ──────────────────────────────

    @staticmethod
    def hash_chain_broken(
        document_id: str,
        broken_at_index: int,
        expected_hash: Optional[str] = None,
        actual_hash: Optional[str] = None,
    ) -> DegradationResult:
        """M8 哈希链断裂降级：报告断裂点 + 阻止写入。

        当防篡改哈希链验证失败时调用，阻止将可能被篡改的内容写入数据库。

        Args:
            document_id: 文档 ID。
            broken_at_index: 断裂发生的块索引。
            expected_hash: 期望的哈希值。
            actual_hash: 实际的哈希值。

        Returns:
            DegradationResult: 降级结果。
        """
        warnings = [
            f"文档 {document_id} 的防篡改哈希链在第 {broken_at_index} 块断裂！",
            "内容完整性校验失败，已阻止写入操作以避免覆盖原始数据。",
            "可能原因：文件被外部程序修改、磁盘错误、或进程间冲突。",
            "建议：立即检查文档来源，从备份恢复或人工审核后再操作。",
        ]

        report = {
            "document_id": document_id,
            "status": "integrity_violation",
            "broken_at_index": broken_at_index,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "action_taken": "write_blocked",
            "recommendation": "人工审核后从备份恢复",
        }

        logger.error(
            "Hash chain broken: doc=%s, index=%d, expected=%s, actual=%s",
            document_id, broken_at_index, expected_hash, actual_hash,
        )
        return DegradationResult(data=report, warnings=warnings)


# 单例
degradation_service = DegradationService()
