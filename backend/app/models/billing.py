"""
Billing models: Subscription, Payment, Invoice, Coupon.

Maps to subscriptions, payments, invoices, coupons tables.
Implements the billing & subscription system.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Numeric, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UniversalUUID

if TYPE_CHECKING:
    from app.models.user import User


class SubscriptionPlan(str, Enum):
    """Subscription plan enum.

    Attributes:
        FREE: Free tier.
        BASIC: Basic plan.
        PRO: Pro plan.
        ENTERPRISE: Enterprise plan.
    """

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Subscription(Base):
    """Subscription model.

    Tracks user subscription status and billing cycle.

    Attributes:
        id: Subscription unique ID (UUID v4, PK).
        user_id: User ID (FK).
        plan: Subscription plan (enum).
        status: Subscription status (active / cancelled / expired / pending).
        auto_renew: Whether auto-renewal is enabled.
        payment_provider: Payment provider name (e.g. "stripe", "wechat").
        started_at: Subscription start time (UTC).
        expires_at: Subscription expiration time (UTC).
        cancelled_at: Cancellation time (UTC, nullable).
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(
        SAEnum(SubscriptionPlan, name="subscription_plan", create_type=False),
        nullable=False,
        default=SubscriptionPlan.FREE,
        server_default="free",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    payment_provider: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscriptions",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="subscription",
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, plan={self.plan.value}, status={self.status})>"


class Payment(Base):
    """Payment model.

    Records individual payment transactions.

    Attributes:
        id: Payment unique ID (UUID v4, PK).
        subscription_id: Associated subscription ID (FK, nullable for one-off payments).
        user_id: User ID (FK).
        amount: Payment amount.
        currency: Currency code (default "CNY").
        provider: Payment provider name.
        provider_payment_id: External payment transaction ID.
        status: Payment status (pending / completed / failed / refunded).
        paid_at: Payment completion time (UTC).
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UniversalUUID,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="CNY",
        server_default="CNY",
    )
    provider: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        back_populates="payments",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="payments",
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="payment",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"


class Invoice(Base):
    """Invoice model.

    Stores invoice metadata for completed payments.

    Attributes:
        id: Invoice unique ID (UUID v4, PK).
        user_id: User ID (FK).
        payment_id: Associated payment ID (FK).
        invoice_number: Unique invoice number.
        pdf_url: Invoice PDF download URL.
        issued_at: Invoice issue time (UTC).
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UniversalUUID,
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        back_populates="invoice",
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number!r})>"


class Coupon(Base):
    """Coupon model.

    Manages discount coupons for subscriptions.

    Attributes:
        id: Coupon unique ID (UUID v4, PK).
        code: Unique coupon code.
        discount_type: Discount type ("percent" / "fixed").
        discount_value: Discount value (percent 0-100, or fixed amount).
        max_uses: Maximum number of uses (0 = unlimited).
        current_uses: Number of times already used.
        expires_at: Expiration time (UTC, nullable for no expiry).
    """

    __tablename__ = "coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    discount_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    max_uses: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
    )
    current_uses: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Coupon(id={self.id}, code={self.code!r})>"
