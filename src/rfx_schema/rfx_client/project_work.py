"""
Project Work Package & Work Item ORM Models (Schema Layer)
=========================================================
Tables linking work packages and work items to specific projects.
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import INTERVAL, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TableBase, SCHEMA
from .types import WorkPackageStatusEnum
from .project import Project
from .work_package import WorkPackage


class ProjectWorkPackage(TableBase):
    """Project work packages in ``rfx_client.project_work_package``."""

    __tablename__ = "project_work_package"
    __table_args__ = (
        # In DB, this is a UNIQUE INDEX with a WHERE clause, not a simple UniqueConstraint
        Index(
            "uq_project_work_package",
            "project_id",
            "work_package_id",
            unique=True,
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        # Other specific indexes from DDL
        Index(
            "idx_pwp_project_id",
            "project_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        Index(
            "idx_pwp_project_not_deleted",
            "project_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        Index(
            "idx_pwp_work_package_id",
            "work_package_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id"),
    )
    work_package_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.work_package._id"),
    )

    quantity: Mapped[Optional[int]] = mapped_column(Integer, default=1)

    work_package_is_custom: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    work_package_name: Mapped[Optional[str]] = mapped_column(String(255))
    work_package_description: Mapped[Optional[str]] = mapped_column(Text)
    work_package_example_description: Mapped[Optional[str]] = mapped_column(Text)
    work_package_complexity_level: Mapped[Optional[int]] = mapped_column(
        Integer, default=1
    )
    work_package_estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)

    status: Mapped[WorkPackageStatusEnum] = mapped_column(
        SQLEnum(WorkPackageStatusEnum, name="workpackageenum", schema=SCHEMA),
        default=WorkPackageStatusEnum.TODO,
        nullable=False,
    )
    date_complete: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when work package was completed (status changed to DONE)",
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="work_packages")
    work_package: Mapped["WorkPackage"] = relationship()
    work_items: Mapped[List["ProjectWorkPackageWorkItem"]] = relationship(
        back_populates="work_package", cascade="all, delete-orphan"
    )


class ProjectWorkItem(TableBase):
    """Project work items in ``rfx_client.project_work_item``."""

    __tablename__ = "project_work_item"
    __table_args__ = (
        Index(
            "idx_pwi_type",
            "type",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id"),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="work_items")
    deliverables: Mapped[List["ProjectWorkItemDeliverable"]] = relationship(
        back_populates="work_item", cascade="all, delete-orphan"
    )


class ProjectWorkPackageWorkItem(TableBase):
    """Links work items to work packages within a project in ``rfx_client.project_work_package_work_item``."""

    __tablename__ = "project_work_package_work_item"
    __table_args__ = (
        UniqueConstraint(
            "project_work_package_id",
            "project_work_item_id",
            name="project-work-package-work-ite_project_work_package_id_proje_key",
        ),
        Index(
            "idx_pwpwi_work_item_id",
            "project_work_item_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    project_work_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project_work_package._id", ondelete="CASCADE"),
        nullable=False,
    )
    project_work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project_work_item._id", ondelete="CASCADE"),
        nullable=False,
    )

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id"),
    )

    # Relationships
    work_package: Mapped["ProjectWorkPackage"] = relationship(
        back_populates="work_items"
    )
    work_item: Mapped["ProjectWorkItem"] = relationship()
    project: Mapped["Project"] = relationship()


class ProjectWorkItemDeliverable(TableBase):
    """Project work item deliverables in ``rfx_client.project_work_item_deliverable``."""

    __tablename__ = "project_work_item_deliverable"
    __table_args__ = (
        Index(
            "idx_pwid_project_work_item_id",
            "project_work_item_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    project_work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project_work_item._id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id"),
    )

    # Relationships
    work_item: Mapped["ProjectWorkItem"] = relationship(back_populates="deliverables")
    project: Mapped["Project"] = relationship()
