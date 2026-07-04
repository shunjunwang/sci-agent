"""
P0-K: 学术规范自查工具 单元测试

覆盖三个核心检查维度：
- check_format（参考文献格式）
- check_structure（章节结构）
- check_citations（引用完整性双向校验）
"""
import pytest
from app.services.academic_checker_service import (
    AcademicCheckerService,
    CheckIssue,
    _check_format,
    _check_structure,
    _check_citations,
    _extract_in_text_citations,
    _extract_reference_ids,
)


class TestReferenceFormat:
    """参考文献格式检查测试。"""

    def test_gbt7714_valid_format(self):
        """GB/T 7714 格式正确的参考文献应通过检查。"""
        refs = [
            "张三, 李四. 深度学习在自然语言处理中的应用[J]. 计算机学报, 2023, 46(3): 456-478.",
            "Smith J, Brown K. Advances in Machine Learning[J]. Nature, 2024, 628(1): 100-120.",
        ]
        issues = _check_format(refs, "gbt7714")
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"不应有错误，实际: {errors}"

    def test_gbt7714_missing_year(self):
        """缺少年份的参考文献应触发警告。"""
        refs = [
            "张三, 李四. 深度学习在自然语言处理中的应用[J]. 计算机学报.",
        ]
        issues = _check_format(refs, "gbt7714")
        year_warnings = [i for i in issues if "年份" in i.message]
        assert len(year_warnings) >= 1

    def test_gbt7714_empty_reference(self):
        """空参考文献应触发警告。"""
        refs = ["", "   "]
        issues = _check_format(refs, "gbt7714")
        empty_warnings = [i for i in issues if "为空" in i.message]
        assert len(empty_warnings) >= 2

    def test_apa_valid_format(self):
        """APA 格式正确的参考文献应通过检查。"""
        refs = [
            "Smith, J., & Brown, K. (2024). Advances in machine learning. Nature, 628(1), 100-120.",
        ]
        issues = _check_format(refs, "apa")
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_unsupported_style(self):
        """不支持的格式应返回错误。"""
        issues = _check_format(["test ref"], "unsupported")
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) >= 1
        assert any("不支持的引用格式" in e.message for e in errors)


class TestStructureCheck:
    """章节结构检查测试。"""

    def test_complete_structure(self):
        """包含所有必需章节应完全通过。"""
        headings = [
            "Abstract",
            "Introduction",
            "Related Work",
            "Method",
            "Results and Analysis",
            "Discussion",
            "Conclusion",
            "References",
        ]
        issues = _check_structure(headings)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"不应有错误，实际: {errors}"

    def test_chinese_structure(self):
        """中文标题也应当被正确识别。"""
        headings = [
            "摘要",
            "引言",
            "相关工作",
            "实验方法",
            "结果分析",
            "讨论",
            "结论",
            "参考文献",
        ]
        issues = _check_structure(headings)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_missing_method_section(self):
        """缺少方法章节应报告错误。"""
        headings = [
            "Abstract",
            "Introduction",
            "Results",
            "Discussion",
            "Conclusion",
        ]
        issues = _check_structure(headings)
        errors = [i for i in issues if i.severity == "error"]
        method_issues = [e for e in errors if "方法" in e.message or "Method" in e.message]
        assert len(method_issues) >= 1

    def test_missing_optional_sections(self):
        """缺少推荐章节应触发警告而非错误。"""
        headings = [
            "Introduction",
            "Method",
            "Results",
            "Discussion",
            "Conclusion",
        ]
        issues = _check_structure(headings)
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) > 0
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_minimal_acceptable_structure(self):
        """仅包含 5 个必需章节应无错误。"""
        headings = [
            "1. Introduction",
            "2. Method",
            "3. Results",
            "4. Discussion",
            "5. Conclusion",
        ]
        issues = _check_structure(headings)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0


class TestCitationIntegrity:
    """引用完整性双向校验测试。"""

    def test_perfect_match(self):
        """正文引用与参考文献完全匹配应无错误。"""
        text = (
            "Machine learning has advanced significantly [1]. "
            "Recent work [2] shows promising results. "
            "However, some challenges remain [3]."
        )
        refs = [
            "[1] Smith J. A survey of ML. Nature, 2023.",
            "[2] Brown K. Deep learning progress. Science, 2024.",
            "[3] Lee M. Challenges in AI. AI Journal, 2024.",
        ]
        issues = _check_citations(text, refs, style="numeric")
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"不应有错误，实际: {errors}"

    def test_orphan_citation(self):
        """正文引用了但文献列表中没有对应条目。"""
        text = "As shown in [1] and [99]..."
        refs = [
            "[1] Smith J. A survey. Nature, 2023.",
        ]
        issues = _check_citations(text, refs, style="numeric")
        errors = [i for i in issues if i.severity == "error"]
        orphan = [e for e in errors if "99" in e.message]
        assert len(orphan) >= 1

    def test_unused_reference(self):
        """文献列表中有但正文未引用。"""
        text = "As shown in [1]..."
        refs = [
            "[1] Smith J. A survey. Nature, 2023.",
            "[2] Brown K. Unused paper. Science, 2024.",
        ]
        issues = _check_citations(text, refs, style="numeric")
        warnings = [i for i in issues if i.severity == "warning"]
        unused = [w for w in warnings if "未被引用" in w.message or "2" in w.message]
        assert len(unused) >= 1

    def test_non_sequential_numeric(self):
        """不连续的引用编号应触发警告。"""
        text = "As shown in [1] and [5]..."
        refs = [
            "[1] Smith J. Paper 1. Nature, 2023.",
            "[5] Brown K. Paper 5. Science, 2024.",
        ]
        issues = _check_citations(text, refs, style="numeric")
        seq_warnings = [i for i in issues if "不连续" in i.message]
        assert len(seq_warnings) >= 1

    def test_empty_input_no_crash(self):
        """空输入不应抛出异常。"""
        issues = _check_citations("", [], style="numeric")
        assert isinstance(issues, list)

    def test_citation_extraction_range(self):
        """范围引用 [1-3] 应被正确展开。"""
        text = "References [1-3] cover this topic."
        cites = _extract_in_text_citations(text)
        assert "1" in cites
        assert "2" in cites
        assert "3" in cites

    def test_citation_extraction_comma(self):
        """逗号分隔引用 [1,3,5] 应被正确提取。"""
        text = "See [1,3,5] for details."
        cites = _extract_in_text_citations(text)
        assert "1" in cites
        assert "3" in cites
        assert "5" in cites


class TestAcademicCheckerService:
    """AcademicCheckerService 集成测试。"""

    def test_check_format_integration(self):
        service = AcademicCheckerService()
        refs = [
            "张三. 深度学习综述[J]. 计算机学报, 2023, 46(3): 100-200.",
            "bad reference without year",
        ]
        result = service.check_format(refs, style="gbt7714")
        assert result.passed is True  # warnings 不阻塞通过
        assert result.total_checks == 2
        assert len(result.warnings) >= 1

    def test_check_structure_integration(self):
        service = AcademicCheckerService()
        headings = ["Introduction", "Methods", "Results", "Discussion"]
        result = service.check_structure(headings)
        # 缺少 Conclusion（错误）和推荐章节（警告）
        assert result.passed is False
        assert any("结论" in e.message or "Conclusion" in e.message for e in result.errors)

    def test_check_citations_integration(self):
        service = AcademicCheckerService()
        text = "See [1] and [3] for details."
        refs = [
            "[1] Smith J. Paper one. Nature, 2023.",
            "[2] Doe J. Paper two. Science, 2024.",
        ]
        result = service.check_citations(text, refs, style="numeric")
        # [3] 在参考文献中没有，[2] 在正文中没有
        assert result.passed is False
        assert len(result.errors) >= 1
        assert len(result.warnings) >= 1
