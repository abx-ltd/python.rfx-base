"""
Work Package & Work Item ORM Models (Schema Layer)
==================================================
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INTERVAL, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA


class WorkPackage(TableBase):
    """Work package templates stored in ``rfx_client.work_package``."""

    __tablename__ = "work_package"
    __table_args__ = {"schema": SCHEMA}

    work_package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    example_description: Mapped[Optional[str]] = mapped_column(Text)

    complexity_level: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    total_ar_credits: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    total_de_credits: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    total_op_credits: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    total_credits: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    credits_consumed: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    credits_remaining: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), default=0
    )

    # Relationships
    work_items: Mapped[List["WorkPackageWorkItem"]] = relationship(
        back_populates="work_package", cascade="all, delete-orphan"
    )


class WorkItem(TableBase):
    """Work item templates stored in ``rfx_client.work_item``."""

    __tablename__ = "work_item"
    __table_args__ = {"schema": SCHEMA}

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    estimated_units: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    estimated_credits: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), default=0
    )
    actual_units_consumed: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), default=0
    )
    actual_credits_consumed: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), default=0
    )

    # Relationships
    deliverables: Mapped[List["WorkItemDeliverable"]] = relationship(
        back_populates="work_item", cascade="all, delete-orphan"
    )


class WorkPackageWorkItem(TableBase):
    """Link work items to work packages in ``rfx_client.work_package_work_item``."""

    __tablename__ = "work_package_work_item"
    __table_args__ = (
        UniqueConstraint(
            "work_package_id",
            "work_item_id",
            name="work-package-work-item_work_package_id_work_item_id_key",
        ),
        {"schema": SCHEMA},
    )

    work_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.work_package._id", ondelete="CASCADE"),
        nullable=False,
    )
    work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.work_item._id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    work_package: Mapped["WorkPackage"] = relationship(back_populates="work_items")
    work_item: Mapped["WorkItem"] = relationship()


class WorkItemDeliverable(TableBase):
    """Work item deliverables stored in ``rfx_client.work_item_deliverable``."""

    __tablename__ = "work_item_deliverable"
    __table_args__ = (
        UniqueConstraint("work_item_id", name="uq_deliverable_work_item_active"),
        {"schema": SCHEMA},
    )

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.work_item._id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    work_item: Mapped["WorkItem"] = relationship(back_populates="deliverables")
