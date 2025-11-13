"""
Credit Management ORM Models (Schema Layer)
===========================================
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA


class CreditBalance(TableBase):
    """Credit balance tracking in ``rfx_client.credit_balance``."""

    __tablename__ = "credit_balance"
    __table_args__ = (
        UniqueConstraint("organization_id", name="credit_balance_organization_id_key"),
        CheckConstraint("ar_credits >= 0", name="ck_ar_credits_positive"),
        CheckConstraint("de_credits >= 0", name="ck_de_credits_positive"),
        CheckConstraint("op_credits >= 0", name="ck_op_credits_positive"),
        CheckConstraint("total_credits >= 0", name="ck_total_credits_positive"),
        CheckConstraint(
            "total_credits = (ar_credits + de_credits + op_credits)",
            name="ck_total_credits_sum",
        ),
        {"schema": SCHEMA},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    ar_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    de_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    op_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_credits: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, nullable=False
    )

    total_purchased_credits: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, nullable=False
    )
    total_used: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_refunded_credits: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, nullable=False
    )

    last_purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_usage_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_refund_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    avg_daily_usage: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, nullable=False
    )
    avg_weekly_usage: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, nullable=False
    )

    estimated_depletion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    days_until_depleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_low_balance: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    low_balance_threshold: Mapped[float] = mapped_column(
        Numeric(12, 2), default=100, nullable=False
    )


class CreditPackage(TableBase):
    """Credit packages stored in ``rfx_client.credit_package``."""

    __tablename__ = "credit_package"
    __table_args__ = (
        UniqueConstraint("package_code", name="credit_package_package_code_key"),
        UniqueConstraint("package_name", name="credit_package_package_name_key"),
        {"schema": SCHEMA},
    )

    package_name: Mapped[str] = mapped_column(String(100), nullable=False)
    package_code: Mapped[str] = mapped_column(String(50), nullable=False)

    ar_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    de_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    op_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_credits: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text)
    features: Mapped[Optional[dict]] = mapped_column(JSONB)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)


class CreditPurchase(TableBase):
    """Credit purchase history in ``rfx_client.credit_purchase``."""

    __tablename__ = "credit_purchase"
    __table_args__ = (
        UniqueConstraint("transaction_id", name="credit_purchase_transaction_id_key"),
        UniqueConstraint("invoice_number", name="credit_purchase_invoice_number_key"),
        {"schema": SCHEMA},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    purchased_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    ar_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    de_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    op_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_credits: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    discount_code: Mapped[Optional[str]] = mapped_column(String(50))
    discount_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    final_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    package_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.credit_package._id")
    )

    payment_gateway: Mapped[Optional[str]] = mapped_column(String(50))
    payment_gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB)

    refund_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refund_reason: Mapped[Optional[str]] = mapped_column(Text)
    refunded_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    package: Mapped[Optional["CreditPackage"]] = relationship()


class CreditUsageLog(TableBase):
    """Credit usage tracking in ``rfx_client.credit_usage_log``."""

    __tablename__ = "credit_usage_log"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    work_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    work_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    work_type: Mapped[str] = mapped_column(String(50), nullable=False)
    credits_used: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    credit_per_unit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    units_consumed: Mapped[float] = mapped_column(
        Numeric(12, 2), default=1, nullable=False
    )

    usage_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    used_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    work_item_name: Mapped[Optional[str]] = mapped_column(String(255))
    work_package_name: Mapped[Optional[str]] = mapped_column(String(255))
    project_name: Mapped[Optional[str]] = mapped_column(String(255))
    used_by_name: Mapped[Optional[str]] = mapped_column(String(255))
    used_by_email: Mapped[Optional[str]] = mapped_column(String(255))

    description: Mapped[Optional[str]] = mapped_column(Text)

    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refund_reason: Mapped[Optional[str]] = mapped_column(Text)
    refunded_credits: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
