"""
Project-related ORM Models (Schema Layer)
=========================================
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    ForeignKeyConstraint, # <--- Cần import cái này
    Integer,
    String,
    Text,
    UniqueConstraint,
    BigInteger,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import INTERVAL, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import PriorityEnum, SyncStatusEnum, ContactMethodEnum


class Project(TableBase):
    """Core project entity stored in ``rfx_client.project``."""

    __tablename__ = "project"
    __table_args__ = (
        Index("idx_project_referral_code", "referral_code_used"),
        {"schema": SCHEMA},
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))

    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priorityenum", schema=SCHEMA), nullable=False
    )
    status: Mapped[str] = mapped_column(String(100), nullable=False)

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration: Mapped[Optional[str]] = mapped_column(INTERVAL)
    duration_text: Mapped[Optional[str]] = mapped_column(String(255))

    free_credit_applied: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    referral_code_used: Mapped[Optional[str]] = mapped_column(String(50))

    sync_status: Mapped[Optional[SyncStatusEnum]] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA),
        default=SyncStatusEnum.PENDING,
        # Fix: Thêm server_default để khớp với DDL
        server_default=text("'PENDING'::cpo_client.syncstatusenum")
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    members: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    work_packages: Mapped[List["ProjectWorkPackage"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["ProjectWorkItem"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    milestones: Mapped[List["ProjectMilestone"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    bdm_contacts: Mapped[List["ProjectBDMContact"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    documents: Mapped[List["ProjectDocument"]] = (
        relationship(  
            back_populates="project", cascade="all, delete-orphan"
        )
    )


class ProjectMember(TableBase):
    """Project membership stored in ``rfx_client.project_member``."""

    __tablename__ = "project_member"
    __table_args__ = (
        Index(
            "uq_project_member_active",
            "project_id",
            "member_id",
            unique=True,
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.project._id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    role: Mapped[str] = mapped_column(String(100), nullable=False)
    permission: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")


class ProjectMilestone(TableBase):
    """Project milestones stored in ``rfx_client.project_milestone``."""

    __tablename__ = "project_milestone"
    __table_args__ = {"schema": SCHEMA}

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.project._id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    is_completed: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="milestones")


class ProjectBDMContact(TableBase):
    """BDM contact requests stored in ``rfx_client.project_bdm_contact``."""

    __tablename__ = "project_bdm_contact"
    __table_args__ = {"schema": SCHEMA}

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.project._id"), nullable=False
    )

    contact_method: Mapped[ContactMethodEnum] = mapped_column(
        SQLEnum(ContactMethodEnum, name="contactmethodenum", schema=SCHEMA),
        nullable=False,
    )
    message: Mapped[Optional[str]] = mapped_column(Text)
    meeting_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="bdm_contacts")


class ProjectDocument(TableBase):
    """Project documents stored in ``rfx_client.project_document``."""

    __tablename__ = "project_document"
    __table_args__ = (
        # FIX: Định nghĩa rõ ràng khóa ngoại thứ 2 đang tồn tại trong DB
        # để Alembic không cố gắng drop nó.
        ForeignKeyConstraint(
            ["project_id"], 
            [f"{SCHEMA}.project._id"], 
            name="project_document_project_id_fkey"
        ),
        Index(
            "idx_project_document_creator",
            "_creator",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        Index(
            "idx_project_document_project",
            "project_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        Index(
            "idx_project_document_status",
            "status",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    # Cột này map với khóa ngoại 'fk_project' (có CASCADE)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project._id", name="fk_project", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    media_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    doc_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="IN_PROGRESS",
        server_default=text("'IN_PROGRESS'::character varying")
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True)
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="documents")
    participants: Mapped[List["ProjectDocumentParticipant"]] = relationship(  # noqa: F821
        back_populates="document", cascade="all, delete-orphan"
    )


class ProjectDocumentParticipant(TableBase):
    """Participants of project documents stored in ``rfx_client.project_document_participant``."""

    __tablename__ = "project_document_participant"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "participant_id", name="unique_doc_participant"
        ),
        Index(
            "idx_document_participant",
            "document_id",
            postgresql_where=text("(_deleted IS NULL)"),
        ),
        {"schema": SCHEMA},
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project_document._id", ondelete="CASCADE"),
        nullable=False,
    )

    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="REVIEWER",
        server_default=text("'REVIEWER'::character varying")
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    document: Mapped["ProjectDocument"] = relationship(back_populates="participants")