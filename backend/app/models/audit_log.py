"""
M8 - 防篡改日志 ORM 模型

交付物来源: task-pc1-m8
注意: 主项目已有 models/activity.py (ActivityLog, 轻量事件日志)，
      此文件为 M8 哈希链审计日志的独立实现，映射到不同表。
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, JSON, Index,
)

from app.core.database import Base


class AuditLogM8(Base):
    """研学行为审计日志 — 哈希链防篡改，只追加不修改不删除"""

    __tablename__ = "activity_logs_m8"
    __table_args__ = (
        Index("idx_audit_m8_user_type_time", "user_id", "action_type", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True, comment="UUID 字符串")
    action_type = Column(
        String(50),
        nullable=False,
        comment="search / read / write / sandbox / submit / login / logout / register / share / invite",
    )
    action_detail = Column(JSON, nullable=False, default={})
    prev_hash = Column(String(128), nullable=False)
    current_hash = Column(String(128), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLogM8(id={self.id[:8]}..., user={self.user_id[:8]}..., action='{self.action_type}')>"


class IntegrityCheckM8(Base):
    """完整性校验报告"""

    __tablename__ = "integrity_checks_m8"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_uid = Column(String(64), unique=True, nullable=False, index=True)
    scope_user_id = Column(String(36), nullable=True)
    scope_date_from = Column(DateTime, nullable=True)
    scope_date_to = Column(DateTime, nullable=True)
    total_logs = Column(Integer, nullable=False)
    verified_logs = Column(Integer, nullable=False)
    broken_chains = Column(Integer, nullable=False)
    anomalies = Column(Integer, nullable=False)
    hash_chain_status = Column(
        String(20),
        nullable=False,
        comment="HEALTHY / DEGRADED / BROKEN",
    )
    details = Column(JSON, default=[])
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<IntegrityCheckM8(report='{self.report_uid}', status='{self.hash_chain_status}')>"
