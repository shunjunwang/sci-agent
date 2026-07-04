"""
P2-12: 工作流实例持久化模型

存储工作流执行实例的状态、已完成步骤、当前进度等。
支持断点续跑——用户关闭浏览器后重新打开可恢复进度。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowInstance(Base):
    """工作流实例 — 持久化工作流执行状态。

    每个用户可同时运行多个工作流实例（不同工作流类型或不同课题）。
    """

    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    workflow_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="工作流类型（如 phd_proposal）"
    )
    instance_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="实例别名（用户自定义）"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        comment="总体状态：pending / running / completed / failed / cancelled",
    )
    completed_steps: Mapped[list] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
        comment="已完成的 step_id 列表",
    )
    current_step: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="当前正在执行的 step_id"
    )
    step_results: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        server_default="{}",
        comment="各步骤执行结果，key=step_id, value={status, output, error, started_at, completed_at}",
    )
    total_steps: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="工作流总步骤数"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def progress_pct(self) -> float:
        """完成进度百分比。"""
        if self.total_steps == 0:
            return 0.0
        return len(self.completed_steps or []) / self.total_steps * 100

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def __repr__(self) -> str:
        return (
            f"<WorkflowInstance(id={self.id}, type={self.workflow_type!r}, "
            f"status={self.status!r})>"
        )
