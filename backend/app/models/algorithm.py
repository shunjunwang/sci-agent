"""
M9 - 算法商城 ORM 模型

交付物来源: task-pc3-m9
映射到 algorithms / algorithm_reviews / algorithm_executions 表。
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Float, DateTime, JSON, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.sandbox import SandboxJob  # type: ignore[attr-defined]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Algorithm(Base):
    """算法模板"""

    __tablename__ = "algorithms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    docker_image: Mapped[str] = mapped_column(String(255), nullable=False)
    input_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    default_params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, onupdate=_now_utc, nullable=False)

    # 关系
    author: Mapped["User"] = relationship("User", backref="algorithms")
    reviews: Mapped[List["AlgorithmReview"]] = relationship("AlgorithmReview", back_populates="algorithm", cascade="all, delete-orphan")
    executions: Mapped[List["AlgorithmExecution"]] = relationship("AlgorithmExecution", back_populates="algorithm", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Algorithm(id={self.id[:8]}..., name='{self.name}', category='{self.category}')>"


class AlgorithmReview(Base):
    """算法评价"""

    __tablename__ = "algorithm_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    algorithm_id: Mapped[str] = mapped_column(String(36), ForeignKey("algorithms.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    __table_args__ = (
        UniqueConstraint("algorithm_id", "user_id", name="uq_algorithm_review_user"),
    )

    algorithm: Mapped["Algorithm"] = relationship("Algorithm", back_populates="reviews")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AlgorithmReview(id={self.id[:8]}..., algorithm_id={self.algorithm_id[:8]}..., rating={self.rating})>"


class AlgorithmExecution(Base):
    """算法执行记录"""

    __tablename__ = "algorithm_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    algorithm_id: Mapped[str] = mapped_column(String(36), ForeignKey("algorithms.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    sandbox_job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sandbox_jobs.id"), nullable=True, index=True)
    params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        comment="queued / running / completed / failed / timeout",
    )
    execution_time: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    algorithm: Mapped["Algorithm"] = relationship("Algorithm", back_populates="executions")
    user: Mapped["User"] = relationship("User")
    sandbox_job: Mapped["SandboxJob"] = relationship("SandboxJob")

    def __repr__(self) -> str:
        return f"<AlgorithmExecution(id={self.id[:8]}..., algorithm_id={self.algorithm_id[:8]}..., status='{self.status}')>"
