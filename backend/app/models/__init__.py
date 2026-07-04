"""
SQLAlchemy ORM 模型包。

导入所有模型以确保 Base.metadata 包含全部表定义，
Alembic 迁移和 create_all() 可自动发现。
"""

from app.core.database import Base

from app.models.user import User, SubscriptionPlan
from app.models.paper import Paper, PaperSource, SearchHistory
from app.models.library import UserLibrary
from app.models.annotation import Annotation
from app.models.document import Document
from app.models.sandbox import SandboxSession, SandboxStatus
from app.models.sandbox_job import SandboxJob
from app.models.workspace import (
    Workspace, WorkspaceMember, Invitation,
    WorkspaceLegacy, WorkspaceMemberLegacy, WorkspaceRole,
)
from app.models.activity import ActivityLog, LogAction
from app.models.audit_log import AuditLogM8, IntegrityCheckM8
from app.models.model_gateway import ModelProvider, UserModelConfig
from app.models.billing import Subscription, Payment, Invoice, Coupon
from app.models.conversation import Conversation
from app.models.writing import WritingDocument, ContentTrace, WritingPlan
from app.models.algorithm import Algorithm, AlgorithmReview, AlgorithmExecution
from app.models.token_blacklist import TokenBlacklist

__all__ = [
    # Base
    "Base",
    # User
    "User",
    "SubscriptionPlan",
    # Paper
    "Paper",
    "PaperSource",
    "SearchHistory",
    # Library
    "UserLibrary",
    # Annotation
    "Annotation",
    # Document
    "Document",
    # Sandbox
    "SandboxSession",
    "SandboxStatus",
    "SandboxJob",
    # Workspace
    "Workspace",
    "WorkspaceMember",
    "Invitation",
    "WorkspaceLegacy",
    "WorkspaceMemberLegacy",
    "WorkspaceRole",
    # Activity
    "ActivityLog",
    "LogAction",
    "AuditLogM8",
    "IntegrityCheckM8",
    # Model Gateway
    "ModelProvider",
    "UserModelConfig",
    # Billing
    "Subscription",
    "Payment",
    "Invoice",
    "Coupon",
    # Conversation
    "Conversation",
    # Writing (M5)
    "WritingDocument",
    "ContentTrace",
    "WritingPlan",
    # Algorithm (M9)
    "Algorithm",
    "AlgorithmReview",
    "AlgorithmExecution",
    # Token Blacklist (P0-1)
    "TokenBlacklist",
]
