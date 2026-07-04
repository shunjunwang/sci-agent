"""
P0-D: 原子级溯源引擎

从段落级"本段为 AI 生成"升级到句子级"这段综合了文献[1]的结论和文献[3]的方法"。
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TraceType(str, Enum):
    """溯源类型枚举。"""
    DIRECT_CITATION = "direct_citation"    # 直接引用（句子含 [1] 标记）
    METHOD_FROM = "method_from"           # "该方法来自文献[3]"
    CONCLUSION_FROM = "conclusion_from"   # "该结论来自文献[1]"
    AI_SYNTHESIS = "ai_synthesis"         # AI 综合归纳（多文献交叉）
    AI_ORIGINAL = "ai_original"           # AI 独立生成（无明确文献依据）


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SentenceTrace:
    """单句溯源记录。"""
    sentence: str
    ref_ids: List[int] = field(default_factory=list)
    trace_type: TraceType = TraceType.AI_ORIGINAL
    confidence: Confidence = Confidence.LOW

    def to_dict(self) -> dict:
        return {
            "sentence": self.sentence,
            "ref_ids": self.ref_ids,
            "type": self.trace_type.value,
            "confidence": self.confidence.value,
        }


@dataclass
class TraceResult:
    """完整溯源结果。"""
    total_sentences: int = 0
    traced_sentences: int = 0
    source_summary: Dict[str, int] = field(default_factory=dict)
    annotations: List[SentenceTrace] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_sentences": self.total_sentences,
            "traced_sentences": self.traced_sentences,
            "source_summary": self.source_summary,
            "annotations": [a.to_dict() for a in self.annotations],
        }


class AtomicTraceEngine:
    """原子级溯源引擎。

    逐句拆解 AI 生成内容，通过以下策略推断每句的文献来源：
    1. 正则提取显式引用标记（[1], [2], [1,3,5] 等）
    2. 关键词语义推断（"该方法"、"结果表明"、"X 等人"）
    3. 无法确定来源的标记为 AI 独立生成
    """

    # 显式引用模式：[1], [2,3], [1-3], [4,5,6]
    CITATION_PATTERN = re.compile(
        r"\[(\d+(?:[,，\-–—]\d+)*)\]"
    )

    # 推断性引用关键词 → TraceType 映射
    INFERENCE_KEYWORDS = [
        (re.compile(r"(该方法|该算法|该模型|该框架).*(来自|源自|基于|出自|参考)"), TraceType.METHOD_FROM),
        (re.compile(r"(实验结果|研究表明|结果(?:表明|显示)|结论(?:表明|指出)).*(文献|论文|研究)"), TraceType.CONCLUSION_FROM),
        (re.compile(r"(综合|结合|融合|集成).*(以上|上述|多个|多种|多篇)"), TraceType.AI_SYNTHESIS),
        (re.compile(r"(文献\[|研究\[|X\s*等人?|et\s*al)"), TraceType.DIRECT_CITATION),
    ]

    # 句子分割模式
    SENTENCE_PATTERN = re.compile(
        r"[^。！？.!?\n]+[。！？.!?\n]+|[^。！？.!?\n]+$"
    )

    @classmethod
    def _split_sentences(cls, content: str) -> List[str]:
        """将文本按句子分割。"""
        if not content:
            return []
        sentences = cls.SENTENCE_PATTERN.findall(content)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def _extract_citation_ids(cls, sentence: str, valid_ref_ids: List[int]) -> List[int]:
        """从句子中提取显式引用 ID。

        Args:
            sentence: 句子文本。
            valid_ref_ids: 可用的文献 ID 列表，用于过滤无效引用。

        Returns:
            去重后的有效引用 ID 列表。
        """
        ids: set[int] = set()
        for match in cls.CITATION_PATTERN.finditer(sentence):
            raw = match.group(1)
            # 展开 [1-3] 范围
            if "-" in raw or "–" in raw or "—" in raw:
                parts = re.split(r"[-–—]", raw)
                if len(parts) == 2:
                    try:
                        start, end = int(parts[0]), int(parts[1])
                        ids.update(range(start, end + 1))
                    except ValueError:
                        pass
            else:
                for part in re.split(r"[,，]", raw):
                    try:
                        ids.add(int(part.strip()))
                    except ValueError:
                        pass

        valid_set = set(valid_ref_ids) if valid_ref_ids else ids
        return sorted(ids & valid_set) if valid_ref_ids else sorted(ids)

    @classmethod
    def _infer_trace_type(
        cls, sentence: str, extracted_ids: List[int], valid_ref_ids: List[int]
    ) -> tuple:
        """推断句子的溯源类型和置信度。

        Returns:
            (TraceType, Confidence, List[int] inferred_ids)
        """
        # 有显式引用 → 直接引用
        if extracted_ids:
            return TraceType.DIRECT_CITATION, Confidence.HIGH, extracted_ids

        # 有关键词推断
        for pattern, trace_type in cls.INFERENCE_KEYWORDS:
            if pattern.search(sentence):
                if trace_type == TraceType.AI_SYNTHESIS:
                    return trace_type, Confidence.MEDIUM, valid_ref_ids[:3] if valid_ref_ids else []
                return trace_type, Confidence.MEDIUM, []

        # 无任何线索 → AI 独立生成
        return TraceType.AI_ORIGINAL, Confidence.LOW, []

    @classmethod
    def trace_section(
        cls,
        content: str,
        references: Optional[List[dict]] = None,
    ) -> TraceResult:
        """对一段 AI 生成内容进行原子级溯源。

        Args:
            content: AI 生成的文本内容。
            references: 可用参考文献列表，每项含 "id" 字段。

        Returns:
            TraceResult: 包含逐句标注的溯源结果。
        """
        if not content:
            return TraceResult()

        # 提取有效引用 ID 列表
        valid_ref_ids = []
        if references:
            for r in references:
                rid = r.get("id", "")
                if isinstance(rid, int):
                    valid_ref_ids.append(rid)
                elif isinstance(rid, str) and rid.isdigit():
                    valid_ref_ids.append(int(rid))

        sentences = cls._split_sentences(content)
        annotations: List[SentenceTrace] = []
        summary: Dict[str, int] = {}

        for sentence in sentences:
            # 1. 提取显式引用 ID
            extracted_ids = cls._extract_citation_ids(sentence, valid_ref_ids)

            # 2. 推断溯源类型
            trace_type, confidence, inferred_ids = cls._infer_trace_type(
                sentence, extracted_ids, valid_ref_ids
            )
            final_ids = extracted_ids if extracted_ids else inferred_ids

            trace = SentenceTrace(
                sentence=sentence,
                ref_ids=final_ids,
                trace_type=trace_type,
                confidence=confidence,
            )
            annotations.append(trace)

            # 统计
            key = trace_type.value
            summary[key] = summary.get(key, 0) + 1

        return TraceResult(
            total_sentences=len(sentences),
            traced_sentences=sum(
                1 for a in annotations if a.trace_type != TraceType.AI_ORIGINAL
            ),
            source_summary=summary,
            annotations=annotations,
        )

    @staticmethod
    def format_trace_annotation(trace_result: TraceResult) -> str:
        """将溯源结果格式化为可读标注。

        例：
        [AI生成] 联邦学习显著提升了模型准确率。
          → 文献[1]实验数据支持 | 置信度:高

        Args:
            trace_result: 溯源结果。

        Returns:
            格式化后的标注文本。
        """
        lines = []
        for t in trace_result.annotations:
            ref_str = ""
            if t.ref_ids:
                ref_str = f"文献[{','.join(str(r) for r in t.ref_ids)}]"

            type_label = {
                TraceType.DIRECT_CITATION: "直接引用",
                TraceType.METHOD_FROM: "方法来源",
                TraceType.CONCLUSION_FROM: "结论来源",
                TraceType.AI_SYNTHESIS: "AI综合归纳",
                TraceType.AI_ORIGINAL: "AI独立生成",
            }.get(t.trace_type, "未知")

            line = f"[{type_label}] {t.sentence}"
            if ref_str:
                line += f"\n  → {ref_str} | 置信度:{t.confidence.value}"
            lines.append(line)

        return "\n".join(lines)


# 模块级便捷实例
trace_engine = AtomicTraceEngine()
