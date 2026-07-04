"""
M6 - Docker仿真沙箱 ORM 模型 (SandboxJob)

交付物来源: task-pc3-m6
映射到 sandbox_jobs 表，记录用户提交的 Docker 沙箱代码执行任务。
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_job_uid(user_id_val: str) -> str:
    raw = f"{user_id_val}:{uuid.uuid4()}:{datetime.now(timezone.utc).isoformat()}"
    return f"job_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


class SandboxJob(Base):
    """沙箱代码执行任务记录"""

    __tablename__ = "sandbox_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    language: Mapped[str] = mapped_column(String(20), nullable=False, comment="python / r")
    code: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        comment="queued / pulling / running / completed / failed / timeout / killed",
    )

    container_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=False)

    cpu_seconds_used: Mapped[float] = mapped_column(Float, default=0.0)
    memory_peak_mb: Mapped[float] = mapped_column(Float, default=0.0)
    gpu_seconds_used: Mapped[float] = mapped_column(Float, default=0.0)

    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_files: Mapped[List] = mapped_column(JSON, default=[])
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    algorithm_executions = relationship("AlgorithmExecution", back_populates="sandbox_job")

    def __repr__(self) -> str:
        return f"<SandboxJob(id={self.id[:8]}..., job_uid='{self.job_uid}', status='{self.status}')>"
