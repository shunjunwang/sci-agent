"""
# mypy: disable-error-code="no-untyped-def"
P0-J: 预编排工作流引擎

5 个典型科研工作流：开题 / 综述 / 复现 / 投稿 / 答辩
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


class WorkflowType(str, Enum):
    PHD_PROPOSAL = "phd_proposal"
    LITERATURE_REVIEW = "lit_review"
    PAPER_REPRODUCTION = "reproduction"
    SUBMISSION_PREP = "submission"
    DEFENSE_PREP = "defense"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    module: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]


class WorkflowEngine:
    """预编排工作流引擎。

    定义、验证、执行（或指导执行）5 种预编排工作流。
    """

    WORKFLOWS: Dict[WorkflowType, WorkflowDefinition] = {}

    def __init__(self):
        self._init_workflows()

    def _init_workflows(self):
        """初始化 5 个预定义工作流。"""

        self.WORKFLOWS = {
            WorkflowType.PHD_PROPOSAL: WorkflowDefinition(
                type=WorkflowType.PHD_PROPOSAL,
                name="博士开题助手",
                description="调研文献 → 分析脉络 → 设计实验 → 写大纲 → 答辩准备",
                steps=[
                    WorkflowStep(
                        "01_search", "文献检索", "M2",
                        "检索近 3 年相关方向综述 + 高引论文", [], {},
                    ),
                    WorkflowStep(
                        "02_import", "导入知识库", "M3",
                        "将检索结果批量导入知识库", ["01_search"], {},
                    ),
                    WorkflowStep(
                        "03_analyze", "研究脉络分析", "M3",
                        "分析文献时间分布 / 机构分布 / 热点演化", ["02_import"], {},
                    ),
                    WorkflowStep(
                        "04_outline", "生成大纲", "M5",
                        "基于文献生成开题报告大纲（Plan 模式）", ["03_analyze"], {},
                    ),
                    WorkflowStep(
                        "05_write", "逐节写作", "M5",
                        "用户确认大纲后逐节展开", ["04_outline"], {},
                    ),
                    WorkflowStep(
                        "06_experiment", "实验设计", "M6",
                        "设计初步实验方案 + 沙箱验证", ["04_outline"], {},
                    ),
                ],
            ),
            WorkflowType.LITERATURE_REVIEW: WorkflowDefinition(
                type=WorkflowType.LITERATURE_REVIEW,
                name="文献综述生成",
                description="多源检索 → 去重入库 → 主题分类 → 大纲 → 逐节生成",
                steps=[
                    WorkflowStep(
                        "01_search", "多源检索", "M2",
                        "arxiv / Semantic Scholar / PubMed 多源检索", [], {},
                    ),
                    WorkflowStep(
                        "02_dedup", "去重入库", "M3",
                        "DOI 去重后批量导入知识库", ["01_search"], {},
                    ),
                    WorkflowStep(
                        "03_classify", "主题分类", "M3",
                        "文献自动分类 + 聚类", ["02_dedup"], {},
                    ),
                    WorkflowStep(
                        "04_outline", "生成大纲", "M5",
                        "基于聚类结果生成综述大纲", ["03_classify"], {},
                    ),
                    WorkflowStep(
                        "05_write", "逐节生成", "M5",
                        "用户确认后逐节生成综述正文", ["04_outline"], {},
                    ),
                ],
            ),
            WorkflowType.PAPER_REPRODUCTION: WorkflowDefinition(
                type=WorkflowType.PAPER_REPRODUCTION,
                name="论文复现助手",
                description="找配套算法 → 沙箱运行 → 结果对比 → 笔记",
                steps=[
                    WorkflowStep(
                        "01_find_algo", "查找配套算法", "M9",
                        "在算法商城中检索论文的配套开源实现", [], {},
                    ),
                    WorkflowStep(
                        "02_sandbox", "沙箱执行", "M6",
                        "在 Docker 沙箱中运行算法", ["01_find_algo"], {},
                    ),
                    WorkflowStep(
                        "03_compare", "结果对比", "M6",
                        "对比复现结果与论文报告数值", ["02_sandbox"], {},
                    ),
                    WorkflowStep(
                        "04_notes", "写入笔记", "M3",
                        "将复现过程和结论写入知识库", ["03_compare"], {},
                    ),
                ],
            ),
            WorkflowType.SUBMISSION_PREP: WorkflowDefinition(
                type=WorkflowType.SUBMISSION_PREP,
                name="投稿准备助手",
                description="期刊推荐 → 格式化 → Cover Letter → 自查",
                steps=[
                    WorkflowStep(
                        "01_recommend", "期刊推荐", "M2",
                        "基于论文标题/摘要推荐匹配期刊", [], {},
                    ),
                    WorkflowStep(
                        "02_format", "格式化", "M5",
                        "按目标期刊模板格式化为 LaTeX", ["01_recommend"], {},
                    ),
                    WorkflowStep(
                        "03_cover_letter", "Cover Letter", "M5",
                        "生成投稿 Cover Letter", ["02_format"], {},
                    ),
                    WorkflowStep(
                        "04_check", "学术规范自查", "M1",
                        "引用格式 / 图表编号 / 数据完整性自查", ["02_format"], {},
                    ),
                ],
            ),
            WorkflowType.DEFENSE_PREP: WorkflowDefinition(
                type=WorkflowType.DEFENSE_PREP,
                name="答辩准备助手",
                description="整理材料 → 生成 PPT → FAQ → 纪要",
                steps=[
                    WorkflowStep(
                        "01_collect", "整理材料", "M3",
                        "整理所有相关论文/实验数据/笔记", [], {},
                    ),
                    WorkflowStep(
                        "02_ppt", "生成 PPT", "M5",
                        "基于材料生成答辩演示文稿", ["01_collect"], {},
                    ),
                    WorkflowStep(
                        "03_faq", "准备 FAQ", "M5",
                        "根据论文内容预测评审问题并准备回答", ["01_collect"], {},
                    ),
                ],
            ),
        }

    # ── 查询 ──────────────────────────────────────

    def get_workflow(self, wf_type: WorkflowType) -> WorkflowDefinition:
        """获取指定工作流定义。"""
        wf = self.WORKFLOWS.get(wf_type)
        if wf is None:
            raise ValueError(f"未知工作流类型: {wf_type}")
        return wf

    def get_all_workflows(self) -> List[WorkflowDefinition]:
        """获取所有工作流列表。"""
        return list(self.WORKFLOWS.values())

    # ── DAG 验证 ──────────────────────────────────

    def validate_dag(self, wf_def: WorkflowDefinition) -> bool:
        """验证工作流 DAG 无循环依赖。

        使用拓扑排序（Kahn 算法）检测。
        """
        step_map = {s.step_id: s for s in wf_def.steps}
        in_degree: Dict[str, int] = {s.step_id: 0 for s in wf_def.steps}
        adjacency: Dict[str, List[str]] = {s.step_id: [] for s in wf_def.steps}

        for step in wf_def.steps:
            for dep in step.dependencies:
                if dep not in step_map:
                    raise ValueError(
                        f"步骤 '{step.step_id}' 依赖不存在的步骤 '{dep}'"
                    )
                adjacency[dep].append(step.step_id)
                in_degree[step.step_id] += 1

        # Kahn 拓扑排序
        queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
        visited = 0

        while queue:
            sid = queue.popleft()
            visited += 1
            for neighbor in adjacency[sid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited == len(wf_def.steps)

    # ── 可执行步骤计算 ────────────────────────────

    def get_executable_steps(
        self,
        wf_def: WorkflowDefinition,
        completed: Set[str],
    ) -> List[WorkflowStep]:
        """获取当前可执行的步骤（依赖已全部满足）。"""
        return [
            step
            for step in wf_def.steps
            if step.step_id not in completed
            and all(dep in completed for dep in step.dependencies)
        ]

    # ── 工作流到 JSON ─────────────────────────────

    def workflow_to_dict(self, wf_def: WorkflowDefinition) -> dict:
        """将工作流定义序列化为字典（供 API 返回）。"""
        return {
            "type": wf_def.type.value,
            "name": wf_def.name,
            "description": wf_def.description,
            "total_steps": len(wf_def.steps),
            "steps": [
                {
                    "step_id": s.step_id,
                    "name": s.name,
                    "module": s.module,
                    "description": s.description,
                    "dependencies": s.dependencies,
                    "config": s.config,
                }
                for s in wf_def.steps
            ],
        }

    # ── P2-12: 持久化实例管理 ──────────────────────

    @staticmethod
    async def create_instance(
        db, user_id: int, wf_type: WorkflowType, instance_name: Optional[str] = None,
    ):
        """创建新工作流实例并持久化。"""
        from app.models.workflow_instance import WorkflowInstance

        wf_def = workflow_engine.get_workflow(wf_type)
        instance = WorkflowInstance(
            user_id=user_id,
            workflow_type=wf_type.value,
            instance_name=instance_name or wf_def.name,
            status="pending",
            total_steps=len(wf_def.steps),
        )
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

    @staticmethod
    async def get_instance(db, instance_id: int):
        """加载持久化的工作流实例。"""
        from sqlalchemy import select
        from app.models.workflow_instance import WorkflowInstance

        result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_instances(db, user_id: int):
        """列出用户所有工作流实例。"""
        from sqlalchemy import select
        from app.models.workflow_instance import WorkflowInstance

        result = await db.execute(
            select(WorkflowInstance)
            .where(WorkflowInstance.user_id == user_id)
            .order_by(WorkflowInstance.updated_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def save_instance_progress(db, instance_id: int, completed_steps: list, current_step: Optional[str] = None):
        """持久化工作流进度。"""
        from sqlalchemy import select
        from app.models.workflow_instance import WorkflowInstance

        result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if instance:
            completed = set(instance.completed_steps or []) | set(completed_steps or [])
            instance.completed_steps = sorted(completed)
            instance.current_step = current_step
            if len(instance.completed_steps) >= instance.total_steps:
                instance.status = "completed"
                instance.completed_at = datetime.now(timezone.utc)
            elif instance.status == "pending":
                instance.status = "running"
                instance.started_at = datetime.now(timezone.utc)
            await db.commit()


# 全局单例
workflow_engine = WorkflowEngine()
