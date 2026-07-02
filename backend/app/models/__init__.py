"""
SQLAlchemy ORM 模型包。

导入所有模型以确保 Base.metadata 包含全部表定义，
Alembic 迁移和 create_all() 可自动发现。
"""

from app.core.database import Base

from app.models.user import User, SubscriptionPlan
from app.models.paper import Paper, PaperSource
from app.models.library import UserLibrary
from app.models.annotation import Annotation
from app.models.document import Document
from app.models.sandbox import SandboxSession, SandboxStatus
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.activity import ActivityLog, LogAction
from app.models.model_gateway import ModelProvider, UserModelConfig
from app.models.billing import Subscription, Payment, Invoice, Coupon
from app.models.conversation import Conversation

__all__ = [
    # Base
    "Base",
    # User
    "User",
    "SubscriptionPlan",
    # Paper
    "Paper",
    "PaperSource",
    # Library
    "UserLibrary",
    # Annotation
    "Annotation",
    # Document
    "Document",
    # Sandbox
    "SandboxSession",
    "SandboxStatus",
    # Workspace
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
    # Activity
    "ActivityLog",
    "LogAction",
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
]
