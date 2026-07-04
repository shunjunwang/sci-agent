"""
P0-K: 学术规范自查服务

三个核心检查维度：
1. format  — 参考文献格式检查（GB/T 7714 / APA / MLA）
2. structure — 论文章节结构检查（引言/方法/结果/讨论/结论）
3. citations — 引用完整性双向校验（正文引用 ↔ 参考文献列表）
"""
import re
from dataclasses import dataclass, field
from typing import List

# ── 数据模型 ───────────────────────────────────────


@dataclass
class CheckIssue:
    """单个检查问题。"""
    severity: str          # error / warning
    message: str           # 人类可读的描述
    location: str          # 位置标识，如 "第 5 条参考文献" 或 "章节: 引言"
    suggestion: str = ""   # 改进建议


@dataclass
class CheckResult:
    """检查结果汇总。"""
    passed: bool
    total_checks: int = 0
    passed_checks: int = 0
    errors: List[CheckIssue] = field(default_factory=list)
    warnings: List[CheckIssue] = field(default_factory=list)
    summary: str = ""


# ── 格式检查 ───────────────────────────────────────

# GB/T 7714 常用文献类型标识
CITATION_TYPES_GBT = {
    "[J]": "期刊文章",
    "[M]": "专著",
    "[C]": "会议论文集",
    "[D]": "学位论文",
    "[P]": "专利",
    "[S]": "标准",
    "[N]": "报纸文章",
    "[EB/OL]": "电子资源",
    "[R]": "报告",
}

# GB/T 7714 基本格式正则（作者. 题名[J]. 刊名, 年, 卷(期): 页码.）
GBT_JOURNAL_PATTERN = re.compile(
    r".+\..+\[[JMCDPSN]\]\..+,\s*\d{4}.*"
)

# APA 基本格式（Author, A. A. (Year). Title. Journal, Volume(Issue), pages.）
APA_PATTERN = re.compile(
    r".+\(\d{4}\)\..+\..+\d+\(\d+\).*\d+.*"
)

# MLA 基本格式（Author. "Title." Journal Volume.Issue (Year): pages.）
MLA_PATTERN = re.compile(
    r".+\..+\..+\d+\.\d+\s*\(\d{4}\).*\d+.*"
)

FORMAT_PATTERNS = {
    "gbt7714": GBT_JOURNAL_PATTERN,
    "apa": APA_PATTERN,
    "mla": MLA_PATTERN,
}


def _check_format(references: List[str], style: str) -> List[CheckIssue]:
    """检查参考文献列表是否符合指定格式。

    Args:
        references: 参考文献字符串列表，每条一项。
        style: 格式风格，gbt7714 / apa / mla。

    Returns:
        CheckIssue 列表。
    """
    issues = []
    pattern = FORMAT_PATTERNS.get(style.lower())

    if not pattern:
        issues.append(CheckIssue(
            severity="error",
            message=f"不支持的引用格式: {style}",
            location="格式检查",
            suggestion="支持的格式: gbt7714, apa, mla",
        ))
        return issues

    for i, ref in enumerate(references):
        ref_stripped = ref.strip()
        if not ref_stripped:
            issues.append(CheckIssue(
                severity="warning",
                message=f"第 {i + 1} 条参考文献为空",
                location=f"参考文献 #{i + 1}",
                suggestion="删除空行或补充引文信息",
            ))
            continue

        # 检查是否匹配格式模式
        if not pattern.search(ref_stripped):
            issues.append(CheckIssue(
                severity="warning",
                message=f"第 {i + 1} 条参考文献格式可能不符合 {style.upper()} 规范",
                location=f"参考文献 #{i + 1}",
                suggestion=f"请按 {style.upper()} 格式核对: {ref_stripped[:80]}...",
            ))

        # 检查年份是否缺失
        if not re.search(r"\d{4}", ref_stripped):
            issues.append(CheckIssue(
                severity="warning",
                message=f"第 {i + 1} 条参考文献可能缺少出版年份",
                location=f"参考文献 #{i + 1}",
                suggestion="请补充四位数字年份（如 2023）",
            ))

    return issues


# ── 结构检查 ───────────────────────────────────────

# 必需章节关键词（中英文）
REQUIRED_SECTIONS = [
    {"name": "引言/Introduction", "keywords": ["引言", "introduction", "背景", "background"]},
    {"name": "方法/Method", "keywords": ["方法", "method", "实验", "experiment", "模型", "model", "算法", "algorithm"]},
    {"name": "结果/Results", "keywords": ["结果", "result", "分析", "analysis", "发现", "finding"]},
    {"name": "讨论/Discussion", "keywords": ["讨论", "discussion", "解释", "interpretation"]},
    {"name": "结论/Conclusion", "keywords": ["结论", "conclusion", "总结", "summary"]},
]

# 可选但推荐的章节
OPTIONAL_SECTIONS = [
    {"name": "摘要/Abstract", "keywords": ["摘要", "abstract"]},
    {"name": "相关工作/Related Work", "keywords": ["相关工作", "related work", "文献综述", "literature review"]},
    {"name": "致谢/Acknowledgments", "keywords": ["致谢", "acknowledgment"]},
    {"name": "参考文献/References", "keywords": ["参考文献", "reference", "bibliography"]},
]


def _check_structure(headings: List[str]) -> List[CheckIssue]:
    """检查论文章节结构是否完整。

    Args:
        headings: 论文各级标题列表。

    Returns:
        CheckIssue 列表。
    """
    issues = []
    headings_lower = [h.lower() for h in headings]

    # 检查必需章节
    for section in REQUIRED_SECTIONS:
        found = any(
            any(kw in h for kw in section["keywords"])
            for h in headings_lower
        )
        if not found:
            issues.append(CheckIssue(
                severity="error",
                message=f"缺少「{section['name']}」章节",
                location="章节结构",
                suggestion=f"学术论文通常需包含 {section['name']} 章节",
            ))

    # 检查推荐章节
    for section in OPTIONAL_SECTIONS:
        found = any(
            any(kw in h for kw in section["keywords"])
            for h in headings_lower
        )
        if not found:
            issues.append(CheckIssue(
                severity="warning",
                message=f"建议增加「{section['name']}」章节",
                location="章节结构",
                suggestion=f"多数期刊要求或推荐包含 {section['name']} 章节",
            ))

    return issues


# ── 引用完整性双向校验 ───────────────────────────

def _extract_in_text_citations(text: str) -> List[str]:
    """从正文中提取引用标记。

    支持格式：
    - 数字型 [1], [1,2,3], [1-3]
    - 作者-年份 (Author, 2020), (Author et al., 2020)
    """
    citations = set()

    # 数字型 [1], [1,2], [1-3], [1,3,5]
    numeric_pattern = re.findall(r"\[([^\]]*)\]", text)
    for match in numeric_pattern:
        # 过滤非引用内容（如 [J]、[M] 等文献类型标记）
        if re.search(r"[JMCDPSN]", match):
            continue
        # 展开范围 [1-3] → ["1", "2", "3"]
        parts = re.split(r"[,;]", match)
        for part in parts:
            part = part.strip()
            if re.match(r"^\d+-\d+$", part):
                start, end = part.split("-")
                for n in range(int(start), int(end) + 1):
                    citations.add(str(n))
            elif re.match(r"^\d+$", part):
                citations.add(part)

    # 作者-年份 (Author, 2020) 或 (Author et al., 2020)
    author_year = re.findall(
        r"\(([^)]*\d{4}[^)]*)\)", text
    )
    for match in author_year:
        citations.add(match.strip())

    return sorted(citations)


def _extract_reference_ids(references: List[str], style: str) -> List[str]:
    """从参考文献列表中提取标识符。

    Args:
        references: 参考文献字符串列表。
        style: 引用风格（numeric / author_year）。

    Returns:
        引用标识符列表。
    """
    ref_ids = []
    for ref in references:
        if style == "numeric":
            # 提取 [1] 或 1. 开头的编号
            m = re.match(r"\[?(\d+)\]?[\.\s]", ref.strip())
            if m:
                ref_ids.append(m.group(1))
        else:
            # 作者-年份：提取第一位作者姓氏 + 年份
            m = re.match(r"([A-Z][a-z]+).*?(\d{4})", ref.strip())
            if m:
                ref_ids.append(f"{m.group(1)}, {m.group(2)}")
            else:
                ref_ids.append(ref.strip()[:50])
    return ref_ids


def _check_citations(
    text: str,
    references: List[str],
    style: str = "numeric",
) -> List[CheckIssue]:
    """双向校验引用完整性。

    Args:
        text: 正文内容。
        references: 参考文献列表。
        style: 引用风格。

    Returns:
        CheckIssue 列表。
    """
    issues = []

    # 提取正文引用和参考文献标识
    in_text_cites = set(_extract_in_text_citations(text))
    ref_ids = _extract_reference_ids(references, style)
    ref_ids_set = set(ref_ids)

    # 1. 正文引用 → 参考文献（正文引用了但文献列表里没有）
    for cite in sorted(in_text_cites):
        if cite not in ref_ids_set:
            # 对于数字型，做更宽松的匹配
            if style == "numeric" and cite.isdigit():
                if str(int(cite)) in ref_ids_set:
                    continue
            issues.append(CheckIssue(
                severity="error",
                message=f"正文引用了 [{cite}] 但在参考文献列表中未找到对应条目",
                location=f"正文引用 [{cite}]",
                suggestion=f"请在参考文献列表中添加 [{cite}] 对应的文献信息",
            ))

    # 2. 参考文献 → 正文引用（文献列表中有但正文没引用）
    for rid in sorted(ref_ids_set):
        if rid not in in_text_cites:
            issues.append(CheckIssue(
                severity="warning",
                message=f"参考文献 [{rid}] 在正文中未被引用",
                location=f"参考文献 #{ref_ids.index(rid) + 1}" if rid in ref_ids else f"参考文献 [{rid}]",
                suggestion="确认该文献是否必要，或在正文中添加引用",
            ))

    # 3. 引用顺序检查（数字型特有）
    if style == "numeric":
        numeric_in_text = sorted(
            [int(c) for c in in_text_cites if c.isdigit()],
        )
        if numeric_in_text:
            expected = list(range(1, len(numeric_in_text) + 1))
            if numeric_in_text != expected:
                issues.append(CheckIssue(
                    severity="warning",
                    message=f"引用编号可能不连续：出现 {numeric_in_text}，期望连续编号 1-{max(numeric_in_text)}",
                    location="引用编号顺序",
                    suggestion="建议按出现顺序重新编号，确保引用连续",
                ))

    return issues


# ── 主服务类 ───────────────────────────────────────


class AcademicCheckerService:
    """学术规范自查服务。

    提供三个维度的检查：格式、结构、引用完整性。
    """

    # ── 参考文献格式检查 ──────────────────────────

    @staticmethod
    def check_format(
        references: List[str],
        style: str = "gbt7714",
    ) -> CheckResult:
        """检查参考文献格式是否符合指定规范。

        Args:
            references: 参考文献列表，每项为一条引文字符串。
            style: 格式规范，支持 gbt7714 / apa / mla。

        Returns:
            CheckResult: 包含所有 issue 的检查结果。
        """
        issues = _check_format(references, style)
        total = len(references)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        passed = len(errors) == 0

        return CheckResult(
            passed=passed,
            total_checks=total,
            passed_checks=total - len(issues),
            errors=errors,
            warnings=warnings,
            summary=(
                f"格式检查完成：{style.upper()} 规范，{total} 条参考文献，"
                f"发现 {len(errors)} 个错误，{len(warnings)} 个警告"
            ),
        )

    # ── 章节结构检查 ──────────────────────────────

    @staticmethod
    def check_structure(
        headings: List[str],
    ) -> CheckResult:
        """检查论文章节结构是否完整。

        Args:
            headings: 论文各级标题列表。

        Returns:
            CheckResult: 包含所有 issue 的检查结果。
        """
        issues = _check_structure(headings)
        total = len(REQUIRED_SECTIONS) + len(OPTIONAL_SECTIONS)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        passed = len(errors) == 0

        return CheckResult(
            passed=passed,
            total_checks=total,
            passed_checks=total - len(issues),
            errors=errors,
            warnings=warnings,
            summary=(
                f"结构检查完成：检查 {total} 项，"
                f"发现 {len(errors)} 个缺失（错误），{len(warnings)} 个建议（警告）"
            ),
        )

    # ── 引用完整性双向校验 ────────────────────────

    @staticmethod
    def check_citations(
        text: str,
        references: List[str],
        style: str = "numeric",
    ) -> CheckResult:
        """双向校验正文引用与参考文献的一致性。

        Args:
            text: 论文正文内容。
            references: 参考文献列表。
            style: 引用风格（numeric / author_year）。

        Returns:
            CheckResult: 包含所有 issue 的检查结果。
        """
        issues = _check_citations(text, references, style)
        total = len(references) + len(_extract_in_text_citations(text))
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        passed = len(errors) == 0

        return CheckResult(
            passed=passed,
            total_checks=max(total, 1),
            passed_checks=total - len(issues),
            errors=errors,
            warnings=warnings,
            summary=(
                f"引用完整性检查完成：{len(references)} 条参考文献，"
                f"发现 {len(errors)} 个未匹配（错误），{len(warnings)} 个未引用（警告）"
            ),
        )


# 单例
academic_checker_service = AcademicCheckerService()
