"""
User ORM 模型。

映射到 users 表，存储科研全流程 AI Agent 平台的用户信息。
兼容 MODEL GATEWAY 方案中的 user_model_configs 外键。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.activity import ActivityLog
    from app.models.annotation import Annotation
    from app.models.billing import Payment, Subscription
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.library import UserLibrary
    from app.models.model_gateway import UserModelConfig
    from app.models.sandbox import SandboxSession
    from app.models.workspace import WorkspaceLegacy, WorkspaceMemberLegacy


class SubscriptionPlan(str, Enum):
    """用户订阅计划枚举。

    Attributes:
        FREE: 免费版。
        BASIC: 基础版。
        PRO: 专业版。
        ENTERPRISE: 企业版。
    """

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """用户角色枚举。

    Attributes:
        USER: 普通用户。
        ADMIN: 管理员。
        SUPER_ADMIN: 超级管理员。
    """

    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """用户模型。

    NOTE: SPEC 中记录 id 为 BIGSERIAL，但本实现采用 UUID 以获得更好的分布式唯一性和安全性。

    Attributes:
        id: 用户唯一标识（UUID v4，主键）。
        email: 邮箱（唯一，索引）。
        hashed_password: bcrypt 哈希后的密码。
        phone: 手机号（加密存储，唯一，可空）。
        wechat_union_id: 微信 UnionID（唯一，可空）。
        full_name: 用户全名。
        institution: 所属机构。
        subscription_plan: 订阅计划（枚举）。
        trial_ends_at: 试用期结束时间（UTC）。
        preferred_language: 首选语言代码，默认 "zh-CN"。
        role: 用户角色（枚举），默认 "user"。
        is_active: 账号是否启用。
        is_verified: 邮箱是否已验证。
        last_login_at: 最后登录时间（UTC）。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
    """

    __tablename__ = "users"

    # NOTE: SPEC 中记录 id 为 BIGSERIAL，但本实现采用 UUID 以获得更好的分布式唯一性和安全性
    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )
    wechat_union_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    institution: Mapped[Optional[str]] = mapped_column(
        String(256),
        default="",
        server_default="",
    )
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        String(50),
        nullable=False,
        default=SubscriptionPlan.FREE,
        server_default="free",
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="zh-CN",
        server_default="zh-CN",
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER,
        server_default="user",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # ── 关系（back_populates）───────────────────────────────────────────────
    # TODO(P3-02): 11 个 relationship 均使用 cascade="all, delete-orphan" 物理删除策略。
    # 后续如需软删除，应改造为被动删除策略（如 on_delete='SET NULL' + 手动清理）。
    # 当前版本无软删除需求，保留物理删除行为。
    user_library: Mapped[List["UserLibrary"]] = relationship(
        "UserLibrary",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    annotations: Mapped[List["Annotation"]] = relationship(
        "Annotation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sandbox_sessions: Mapped[List["SandboxSession"]] = relationship(
        "SandboxSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workspaces_owned: Mapped[List["WorkspaceLegacy"]] = relationship(
        "WorkspaceLegacy",
        foreign_keys="[WorkspaceLegacy.owner_id]",
        back_populates="owner",
    )
    workspace_memberships: Mapped[List["WorkspaceMemberLegacy"]] = relationship(
        "WorkspaceMemberLegacy",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    model_configs: Mapped[List["UserModelConfig"]] = relationship(
        "UserModelConfig",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
