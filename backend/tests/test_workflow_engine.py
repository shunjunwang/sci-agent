"""
P0-J: 预编排工作流 — WorkflowEngine 单元测试

至少 12 个测试。
"""
import pytest

from app.services.workflow_engine import (
    WorkflowEngine,
    WorkflowType,
)


@pytest.fixture
def engine():
    return WorkflowEngine()


class TestWorkflowDefinitions:

    def test_all_workflows_present(self, engine):
        """5 个预定义工作流全部存在。"""
        wfs = engine.get_all_workflows()
        assert len(wfs) == 5
        types = {wf.type for wf in wfs}
        expected = {
            WorkflowType.PHD_PROPOSAL,
            WorkflowType.LITERATURE_REVIEW,
            WorkflowType.PAPER_REPRODUCTION,
            WorkflowType.SUBMISSION_PREP,
            WorkflowType.DEFENSE_PREP,
        }
        assert types == expected

    def test_each_workflow_has_steps(self, engine):
        """每个工作流至少包含 3 个步骤。"""
        for wf in engine.get_all_workflows():
            assert len(wf.steps) >= 3, f"{wf.type} has fewer than 3 steps"

    def test_get_workflow_by_type(self, engine):
        wf = engine.get_workflow(WorkflowType.PHD_PROPOSAL)
        assert wf.name == "博士开题助手"
        assert len(wf.steps) == 6

    def test_invalid_workflow_type_raises(self, engine):
        with pytest.raises(ValueError):
            engine.get_workflow(WorkflowType("nonexistent"))


class TestDAGValidation:

    def test_all_workflows_are_valid_dag(self, engine):
        """所有 5 个预定义工作流 DAG 无环。"""
        for wf in engine.get_all_workflows():
            assert engine.validate_dag(wf), f"{wf.type} DAG is invalid"

    def test_manual_dag_cycle_detected(self, engine):
        """手动构造含环 DAG 应被检测。"""
        from app.services.workflow_engine import WorkflowStep, WorkflowDefinition
        wf = WorkflowDefinition(
            type=WorkflowType.LITERATURE_REVIEW,
            name="Test",
            description="Cycle",
            steps=[
                WorkflowStep("A", "A", "", "", [], {}),
                WorkflowStep("B", "B", "", "", ["A"], {}),
                WorkflowStep("C", "C", "", "", ["B", "C"], {}),  # self-cycle
            ],
        )
        valid = engine.validate_dag(wf)
        assert valid is False

    def test_manual_dag_missing_dep_raises(self, engine):
        """依赖不存在的步骤应抛出异常。"""
        from app.services.workflow_engine import WorkflowStep, WorkflowDefinition
        wf = WorkflowDefinition(
            type=WorkflowType.LITERATURE_REVIEW,
            name="Test",
            description="Bad dep",
            steps=[
                WorkflowStep("A", "A", "", "", [], {}),
                WorkflowStep("B", "B", "", "", ["NONEXISTENT"], {}),
            ],
        )
        with pytest.raises(ValueError, match="NONEXISTENT"):
            engine.validate_dag(wf)


class TestExecutableSteps:

    def test_none_completed_returns_root_nodes(self, engine):
        """无任何完成时，返回无依赖的根步骤。"""
        wf = engine.get_workflow(WorkflowType.LITERATURE_REVIEW)
        executable = engine.get_executable_steps(wf, set())
        assert len(executable) == 1
        assert executable[0].step_id == "01_search"

    def test_partial_completion(self, engine):
        """完成 search 后，dedup 变为可执行。"""
        wf = engine.get_workflow(WorkflowType.LITERATURE_REVIEW)
        executable = engine.get_executable_steps(wf, {"01_search"})
        assert len(executable) == 1
        assert executable[0].step_id == "02_dedup"

    def test_all_completed_returns_empty(self, engine):
        """全部完成后无可执行步骤。"""
        wf = engine.get_workflow(WorkflowType.DEFENSE_PREP)
        all_steps = {s.step_id for s in wf.steps}
        executable = engine.get_executable_steps(wf, all_steps)
        assert len(executable) == 0

    def test_multiple_independent_branches(self, engine):
        """开题工作流中完成 outline 后可执行 write + experiment 两个分支。"""
        wf = engine.get_workflow(WorkflowType.PHD_PROPOSAL)
        completed = {"01_search", "02_import", "03_analyze", "04_outline"}
        executable = engine.get_executable_steps(wf, completed)
        ids = {s.step_id for s in executable}
        assert "05_write" in ids
        assert "06_experiment" in ids


class TestSerialization:

    def test_workflow_to_dict(self, engine):
        wf = engine.get_workflow(WorkflowType.SUBMISSION_PREP)
        d = engine.workflow_to_dict(wf)
        assert d["type"] == "submission"
        assert d["name"] == "投稿准备助手"
        assert len(d["steps"]) == 4
        assert d["steps"][0]["step_id"] == "01_recommend"
        assert "dependencies" in d["steps"][0]
