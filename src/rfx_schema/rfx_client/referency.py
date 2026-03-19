"""
Reference Tables & Support Models (Schema Layer)
================================================
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    DateTime,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.sql import func

from . import TableBase, SCHEMA
from .types import SyncStatusEnum


class Tag(TableBase):
    """Tags stored in ``rfx_client.tag``."""

    __tablename__ = "tag"
    __table_args__ = (
        UniqueConstraint("key", "target_resource", name="uq_tag_target"),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    target_resource: Mapped[str] = mapped_column(String(100), nullable=False)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))


class Status(TableBase):
    """Status definitions in ``rfx_client.status``."""

    __tablename__ = "status"
    __table_args__ = (
        Index("idx_status_entity_type", "entity_type"),
        {"schema": SCHEMA},
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Relationships
    keys: Mapped[List["StatusKey"]] = relationship(
        back_populates="status", cascade="all, delete-orphan"
    )
    transitions: Mapped[List["StatusTransition"]] = relationship(
        back_populates="status", cascade="all, delete-orphan"
    )


class StatusKey(TableBase):
    """Status keys in ``rfx_client.status_key``."""

    __tablename__ = "status_key"
    __table_args__ = (
        UniqueConstraint("status_id", "key", name="uq_status_key"),
        Index("idx_status_key_status", "status_id"),
        {"schema": SCHEMA},
    )

    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.status._id", ondelete="CASCADE"),
        nullable=False,
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    is_initial: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_final: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Relationships
    status: Mapped["Status"] = relationship(back_populates="keys")


class StatusTransition(TableBase):
    """Status transitions in ``rfx_client.status_transition``."""

    __tablename__ = "status_transition"
    __table_args__ = (
        UniqueConstraint(
            "status_id",
            "src_status_key_id",
            "dst_status_key_id",
            name="uq_status_transition",
        ),
        Index("idx_status_transition_status", "status_id"),
        {"schema": SCHEMA},
    )

    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.status._id", ondelete="CASCADE"),
        nullable=False,
    )
    src_status_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.status_key._id", ondelete="CASCADE"),
        nullable=False,
    )
    dst_status_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.status_key._id", ondelete="CASCADE"),
        nullable=False,
    )

    condition: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    status: Mapped["Status"] = relationship(back_populates="transitions")
    src_status: Mapped["StatusKey"] = relationship(foreign_keys=[src_status_key_id])
    dst_status: Mapped["StatusKey"] = relationship(foreign_keys=[dst_status_key_id])


class Promotion(TableBase):
    """Promotions in ``rfx_client.promotion``."""

    __tablename__ = "promotion"
    __table_args__ = (
        UniqueConstraint("code", name="promotion_code_key"),
        Index(
            "idx_promotion_code_valid",
            "code",
            "valid_from",
            "valid_until",
            "current_uses",
            "max_uses",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    max_uses: Mapped[int] = mapped_column(Integer, nullable=False)
    current_uses: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))


class Integration(TableBase):
    """Integration tracking in ``rfx_client.integration``."""

    __tablename__ = "integration"
    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "provider", name="uq_integration_entity"
        ),
        {"schema": SCHEMA},
    )

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(500))

    status: Mapped[SyncStatusEnum] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA), nullable=False
    )


class ProjectIntegration(TableBase):
    """Project integration in ``rfx_client.project_integration``."""

    __tablename__ = "project_integration"
    __table_args__ = {"schema": SCHEMA}

    _etag: Mapped[Optional[str]] = mapped_column(
        String(64), server_default=func.uuid_generate_v4()
    )
    _created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(500))


class ProjectMilestoneIntegration(TableBase):
    """Project milestone integration in ``rfx_client.project_milestone_integration``."""

    __tablename__ = "project_milestone_integration"
    __table_args__ = {"schema": SCHEMA}

    milestone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(500))


class TicketIntegration(TableBase):
    """Ticket integration in ``rfx_client.ticket_integration``."""

    __tablename__ = "ticket_integration"
    __table_args__ = {"schema": SCHEMA}

    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[str] = mapped_column(String(255), nullable=False)


# ============================================================================
# REFERENCE TABLES
# ============================================================================


class RefNotificationType(TableBase):
    """Notification types in ``rfx_client.ref__notification_type``."""

    __tablename__ = "ref__notification_type"
    __table_args__ = {"schema": SCHEMA}

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)


class RefProjectCategory(TableBase):
    """Project categories in ``rfx_client.ref__project_category``."""

    __tablename__ = "ref__project_category"
    __table_args__ = (
        # Fix: Explicitly named to match DB "ref--..." format
        UniqueConstraint("key", name="ref--project-category_key_key"),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)


class RefProjectRole(TableBase):
    """Project roles in ``rfx_client.ref__project_role``."""

    __tablename__ = "ref__project_role"
    __table_args__ = (
        # Fix: Explicitly named to match DB "ref--..." format
        UniqueConstraint("key", name="ref--project-role_key_key"),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)


class RefTicketType(TableBase):
    """Ticket types in ``rfx_client.ref__ticket_type``."""

    __tablename__ = "ref__ticket_type"
    __table_args__ = (
        # Fix: Explicitly named to match DB "ref--..." format
        UniqueConstraint("key", name="ref--ticket-type_key_key"),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_color: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_inquiry: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)


class RefWorkItemType(TableBase):
    """Work item types in ``rfx_client.ref__work_item_type``."""

    __tablename__ = "ref__work_item_type"
    __table_args__ = (
        Index("idx_rt_key", "key"),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    alias: Mapped[Optional[str]] = mapped_column(String(50))
