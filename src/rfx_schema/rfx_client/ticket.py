"""
Ticket Management ORM Models (Schema Layer)
===========================================
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean, Enum as SQLEnum, ForeignKey,
    String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import PriorityEnum, AvailabilityEnum, SyncStatusEnum
from .template_client import Tag


class Ticket(TableBase):
    """Tickets stored in ``rfx_client.ticket``."""

    __tablename__ = "ticket"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priorityenum", schema=SCHEMA),
        nullable=False
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id")
    )
    assignee: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    status: Mapped[str] = mapped_column(String(100), nullable=False)
    availability: Mapped[AvailabilityEnum] = mapped_column(
        SQLEnum(AvailabilityEnum, name="availabilityenum", schema=SCHEMA),
        nullable=False
    )

    sync_status: Mapped[Optional[SyncStatusEnum]] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA),
        default=SyncStatusEnum.PENDING
    )

    is_inquiry: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    parent: Mapped[Optional["Ticket"]] = relationship(
        back_populates="children",
        remote_side="_id"
    )
    children: Mapped[List["Ticket"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    assignees: Mapped[List["TicketAssignee"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    participants: Mapped[List["TicketParticipant"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    tags: Mapped[List["TicketTag"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["TicketStatus"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketAssignee(TableBase):
    """Ticket assignees in ``rfx_client.ticket_assignee``."""

    __tablename__ = "ticket_assignee"
    __table_args__ = (
        UniqueConstraint("ticket_id", "member_id", name="uq_ticket_assignee_active"),
        {"schema": SCHEMA}
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id"),
        nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="assignees")


class TicketParticipant(TableBase):
    """Ticket participants in ``rfx_client.ticket_participant``."""

    __tablename__ = "ticket_participant"
    __table_args__ = (
        UniqueConstraint("ticket_id", "participant_id", name="uq_ticket_participant_active"),
        {"schema": SCHEMA}
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id"),
        nullable=False
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="participants")


class TicketTag(TableBase):
    """Ticket tags in ``rfx_client.ticket_tag``."""

    __tablename__ = "ticket_tag"
    __table_args__ = (
        UniqueConstraint("ticket_id", "tag_id", name="uq_ticket_tag_active"),
        {"schema": SCHEMA}
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id"),
        nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.tag._id"),
        nullable=False
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship()


class TicketStatus(TableBase):
    """Ticket status history in ``rfx_client.ticket_status``."""

    __tablename__ = "ticket_status"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id"),
        nullable=False
    )

    src_state: Mapped[str] = mapped_column(String(100), nullable=False)
    dst_state: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="status_history")


class ProjectTicket(TableBase):
    """Link tickets to projects in ``rfx_client.project_ticket``."""

    __tablename__ = "project_ticket"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id"),
        nullable=False
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.ticket._id"),
        nullable=False
    )