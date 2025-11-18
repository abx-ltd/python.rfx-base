"""
RFX Client View Mappings (Schema Layer)
========================================
Maps database views to SQLAlchemy ORM models for convenient querying.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from . import TableBase, SCHEMA
from .types import PriorityEnum, SyncStatusEnum, AvailabilityEnum


# ============================================================================
# COMMENT VIEWS
# ============================================================================


class CommentView(TableBase):
    """View: _comment - Comments with creator info and counts"""

    __tablename__ = "_comment"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    master_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    content: Mapped[str] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    source: Mapped[Optional[str]] = mapped_column(String)

    creator: Mapped[Optional[dict]] = mapped_column(JSONB)
    attachment_count: Mapped[int] = mapped_column(Integer)
    reaction_count: Mapped[int] = mapped_column(Integer)


class CommentAttachmentView(TableBase):
    """View: _comment_attachment - Comment attachments with media info"""

    __tablename__ = "_comment_attachment"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    media_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    attachment_type: Mapped[Optional[str]] = mapped_column(String(50))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean)

    # Media fields
    filename: Mapped[Optional[str]] = mapped_column(String)
    filehash: Mapped[Optional[str]] = mapped_column(String)
    filemime: Mapped[Optional[str]] = mapped_column(String)
    length: Mapped[Optional[int]] = mapped_column(Integer)
    cdn_url: Mapped[Optional[str]] = mapped_column(String)

    uploader: Mapped[Optional[dict]] = mapped_column(JSONB)


class CommentReactionView(TableBase):
    """View: _comment_reaction - Comment reactions with reactor info"""

    __tablename__ = "_comment_reaction"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reaction_type: Mapped[str] = mapped_column(String(50))
    reactor: Mapped[Optional[dict]] = mapped_column(JSONB)


class CommentReactionSummaryView(TableBase):
    """View: _comment_reaction_summary - Aggregated reaction counts"""

    __tablename__ = "_comment_reaction_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reaction_type: Mapped[str] = mapped_column(String(50))
    reaction_count: Mapped[int] = mapped_column(Integer)
    users: Mapped[List[dict]] = mapped_column(JSONB)


# ============================================================================
# CREDIT VIEWS
# ============================================================================


class CreditSummaryView(TableBase):
    """View: _credit_summary - Organization credit balance summary"""

    __tablename__ = "_credit_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Current balances
    current_ar_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    current_de_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    current_op_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    current_total_credits: Mapped[float] = mapped_column(Numeric(12, 2))

    # Historical totals
    total_purchased_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    total_used: Mapped[float] = mapped_column(Numeric(12, 2))
    total_refunded_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    remaining_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    remaining_percentage: Mapped[float] = mapped_column(Numeric(5, 2))

    # Usage statistics
    avg_daily_usage: Mapped[float] = mapped_column(Numeric(12, 2))
    avg_weekly_usage: Mapped[float] = mapped_column(Numeric(12, 2))
    days_until_depleted: Mapped[int] = mapped_column(Integer)

    # Monthly stats
    month_purchased: Mapped[float] = mapped_column(Numeric(12, 2))
    month_used: Mapped[float] = mapped_column(Numeric(12, 2))

    # Timestamps
    last_purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_usage_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class CreditUsageView(TableBase):
    """View: _credit_usage - Project credit usage by week"""

    __tablename__ = "_credit_usage"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    usage_year: Mapped[int] = mapped_column(Integer)
    usage_week: Mapped[int] = mapped_column(Integer)
    usage_month: Mapped[int] = mapped_column(Integer)
    week_start_date: Mapped[datetime] = mapped_column(DateTime)

    ar_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    de_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    op_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    total_credits: Mapped[float] = mapped_column(Numeric(12, 2))


# ============================================================================
# PROJECT VIEWS
# ============================================================================


class ProjectView(TableBase):
    """View: _project - Projects with member lists and credit totals"""

    __tablename__ = "_project"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priorityenum", schema=SCHEMA)
    )
    status: Mapped[str] = mapped_column(String(100))

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration: Mapped[Optional[str]] = mapped_column(INTERVAL)
    duration_text: Mapped[Optional[str]] = mapped_column(String(255))

    free_credit_applied: Mapped[int] = mapped_column(Integer)
    referral_code_used: Mapped[Optional[str]] = mapped_column(String(50))
    sync_status: Mapped[SyncStatusEnum] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA)
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    members: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    total_credit: Mapped[float] = mapped_column(Numeric(12, 2))
    used_credit: Mapped[float] = mapped_column(Numeric(12, 2))


class ProjectCreditSummaryView(TableBase):
    """View: _project_credit_summary - Per-project credit breakdown"""

    __tablename__ = "_project_credit_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    project_name: Mapped[str] = mapped_column(String(255))
    project_status: Mapped[str] = mapped_column(String)

    total_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    credit_used: Mapped[float] = mapped_column(Numeric(12, 2))
    actual_total_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    credits_remaining: Mapped[float] = mapped_column(Numeric(12, 2))
    completion_percentage: Mapped[float] = mapped_column(Numeric(5, 2))

    total_work_packages: Mapped[int] = mapped_column(Integer)
    completed_work_packages: Mapped[int] = mapped_column(Integer)
    total_work_items: Mapped[int] = mapped_column(Integer)


# ============================================================================
# WORK PACKAGE VIEWS
# ============================================================================


class WorkPackageView(TableBase):
    """View: _work_package - Work packages with credit calculations"""

    __tablename__ = "_work_package"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    work_package_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    example_description: Mapped[Optional[str]] = mapped_column(Text)
    complexity_level: Mapped[int] = mapped_column(Integer)
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)
    is_custom: Mapped[bool] = mapped_column(Boolean)

    type_list: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)))
    work_item_count: Mapped[int] = mapped_column(Integer)

    credits: Mapped[float] = mapped_column(Numeric(12, 2))
    architectural_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    development_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    operation_credits: Mapped[float] = mapped_column(Numeric(12, 2))

    upfront_cost: Mapped[float] = mapped_column(Numeric(12, 2))
    monthly_cost: Mapped[float] = mapped_column(Numeric(12, 2))


class ProjectWorkPackageView(TableBase):
    """View: _project_work_package - Project-specific work packages"""

    __tablename__ = "_project_work_package"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    work_package_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)

    work_package_name: Mapped[Optional[str]] = mapped_column(String(255))
    work_package_is_custom: Mapped[bool] = mapped_column(Boolean)
    work_package_description: Mapped[Optional[str]] = mapped_column(Text)
    work_package_example_description: Mapped[Optional[str]] = mapped_column(Text)
    work_package_complexity_level: Mapped[int] = mapped_column(Integer)
    work_package_estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)

    type_list: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)))
    work_item_count: Mapped[int] = mapped_column(Integer)
    total_deliverables: Mapped[int] = mapped_column(Integer)

    credits: Mapped[float] = mapped_column(Numeric(12, 2))
    architectural_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    development_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    operation_credits: Mapped[float] = mapped_column(Numeric(12, 2))

    upfront_cost: Mapped[float] = mapped_column(Numeric(12, 2))
    monthly_cost: Mapped[float] = mapped_column(Numeric(12, 2))


# ============================================================================
# WORK ITEM VIEWS
# ============================================================================


class WorkItemView(TableBase):
    """View: _work_item - Work items with type aliases"""

    __tablename__ = "_work_item"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)
    type_alias: Mapped[Optional[str]] = mapped_column(String(50))


class ProjectWorkItemView(TableBase):
    """View: _project_work_item - Project-specific work items"""

    __tablename__ = "_project_work_item"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)
    type_alias: Mapped[Optional[str]] = mapped_column(String(50))


# ============================================================================
# TICKET VIEWS
# ============================================================================


class InquiryView(TableBase):
    """View: _inquiry - Inquiry tickets with tags and participants"""

    __tablename__ = "_inquiry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priorityenum", schema=SCHEMA)
    )
    type: Mapped[str] = mapped_column(String(50))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    assignee: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(100))
    availability: Mapped[AvailabilityEnum] = mapped_column(
        SQLEnum(AvailabilityEnum, name="availabilityenum", schema=SCHEMA)
    )
    sync_status: Mapped[SyncStatusEnum] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA)
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    type_icon_color: Mapped[Optional[str]] = mapped_column(String(50))
    tag_names: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    activity: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    participants: Mapped[List[dict]] = mapped_column(ARRAY(JSONB))


class TicketView(TableBase):
    """View: _ticket - Regular tickets linked to projects"""

    __tablename__ = "_ticket"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priorityenum", schema=SCHEMA)
    )
    type: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    assignee: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(100))
    availability: Mapped[AvailabilityEnum] = mapped_column(
        SQLEnum(AvailabilityEnum, name="availabilityenum", schema=SCHEMA)
    )
    sync_status: Mapped[SyncStatusEnum] = mapped_column(
        SQLEnum(SyncStatusEnum, name="syncstatusenum", schema=SCHEMA)
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))


# ============================================================================
# ORGANIZATION VIEWS
# ============================================================================


class OrganizationCreditSummaryView(TableBase):
    """View: _organization_credit_summary - Organization-wide credit overview"""

    __tablename__ = "_organization_credit_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Totals
    total_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    total_purchased_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    total_allocated: Mapped[float] = mapped_column(Numeric(12, 2))
    total_used: Mapped[float] = mapped_column(Numeric(12, 2))
    total_available: Mapped[float] = mapped_column(Numeric(12, 2))

    # AR Credits
    ar_credits_balance: Mapped[float] = mapped_column(Numeric(12, 2))
    ar_credits_allocated: Mapped[float] = mapped_column(Numeric(12, 2))
    ar_credits_used: Mapped[float] = mapped_column(Numeric(12, 2))
    ar_credits_available: Mapped[float] = mapped_column(Numeric(12, 2))

    # DE Credits
    de_credits_balance: Mapped[float] = mapped_column(Numeric(12, 2))
    de_credits_allocated: Mapped[float] = mapped_column(Numeric(12, 2))
    de_credits_used: Mapped[float] = mapped_column(Numeric(12, 2))
    de_credits_available: Mapped[float] = mapped_column(Numeric(12, 2))

    # OP Credits
    op_credits_balance: Mapped[float] = mapped_column(Numeric(12, 2))
    op_credits_allocated: Mapped[float] = mapped_column(Numeric(12, 2))
    op_credits_used: Mapped[float] = mapped_column(Numeric(12, 2))
    op_credits_available: Mapped[float] = mapped_column(Numeric(12, 2))

    # Percentages
    allocation_percentage: Mapped[float] = mapped_column(Numeric(5, 2))
    completion_percentage: Mapped[float] = mapped_column(Numeric(5, 2))

    # Project counts
    total_projects: Mapped[int] = mapped_column(Integer)
    active_projects: Mapped[int] = mapped_column(Integer)

    # Alerts
    is_low_balance: Mapped[bool] = mapped_column(Boolean)
    low_balance_threshold: Mapped[float] = mapped_column(Numeric(12, 2))


class StatusView(TableBase):
    """View: _status - Status keys by entity type"""

    __tablename__ = "_status"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    entity_type: Mapped[str] = mapped_column(String(50))
    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    key: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_initial: Mapped[bool] = mapped_column(Boolean)
    is_final: Mapped[bool] = mapped_column(Boolean)


class OrganizationWeeklyCreditUsageView(TableBase):
    """View: _organization_weekly_credit_usage - Weekly credit usage by organization"""

    __tablename__ = "_organization_weekly_credit_usage"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    week_number: Mapped[int] = mapped_column(Integer)
    week_label: Mapped[str] = mapped_column(String)

    total_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    ar_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    de_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    op_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    work_packages_completed: Mapped[int] = mapped_column(Integer)


# ============================================================================
# WORK ITEM LISTING VIEWS
# ============================================================================


class WorkItemListingView(TableBase):
    """View: _work_item_listing - Work items with package context and calculations"""

    __tablename__ = "_work_item_listing"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    work_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    work_item_name: Mapped[str] = mapped_column(String(255))
    work_item_description: Mapped[Optional[str]] = mapped_column(Text)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    work_item_type_code: Mapped[str] = mapped_column(String(50))
    work_item_type_alias: Mapped[Optional[str]] = mapped_column(String(50))

    total_credits_for_item: Mapped[float] = mapped_column(Numeric(12, 2))
    estimated_cost_for_item: Mapped[float] = mapped_column(Numeric(12, 2))
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)


class ProjectWorkItemListingView(TableBase):
    """View: _project_work_item_listing - Project work items with package context"""

    __tablename__ = "_project_work_item_listing"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    project_work_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    project_work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    project_work_item_name: Mapped[str] = mapped_column(String(255))
    project_work_item_description: Mapped[Optional[str]] = mapped_column(Text)

    price_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    credit_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    project_work_item_type_code: Mapped[str] = mapped_column(String(50))
    project_work_item_type_alias: Mapped[Optional[str]] = mapped_column(String(50))

    total_credits_for_item: Mapped[float] = mapped_column(Numeric(12, 2))
    estimated_cost_for_item: Mapped[float] = mapped_column(Numeric(12, 2))
    estimate: Mapped[Optional[str]] = mapped_column(INTERVAL)


# ============================================================================
# WORK PACKAGE CREDIT USAGE VIEW
# ============================================================================


class WorkPackageCreditUsageView(TableBase):
    """View: _work_package_credit_usage - Work package usage vs estimates with variances"""

    __tablename__ = "_work_package_credit_usage"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    work_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    work_package_name: Mapped[str] = mapped_column(String(255))

    # Estimated credits
    estimated_ar_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    estimated_de_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    estimated_op_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    estimated_total_credits: Mapped[float] = mapped_column(Numeric(12, 2))

    # Actual credits
    actual_ar_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    actual_de_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    actual_op_credits: Mapped[float] = mapped_column(Numeric(12, 2))
    actual_total_credits: Mapped[float] = mapped_column(Numeric(12, 2))

    # Variances
    variance_ar: Mapped[float] = mapped_column(Numeric(12, 2))
    variance_de: Mapped[float] = mapped_column(Numeric(12, 2))
    variance_op: Mapped[float] = mapped_column(Numeric(12, 2))
    variance_total: Mapped[float] = mapped_column(Numeric(12, 2))
    variance_percentage: Mapped[float] = mapped_column(Numeric(5, 2))

    # Progress
    completion_percentage: Mapped[float] = mapped_column(Numeric(5, 2))
    credits_remaining: Mapped[float] = mapped_column(Numeric(12, 2))

    # Work item stats
    total_work_items: Mapped[int] = mapped_column(Integer)
    completed_work_items: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50))


class ProjectDocumentView(TableBase):
    """View: _project_document - Project documents with participants and file metadata"""

    __tablename__ = "_project_document"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # Document info
    document_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    doc_type: Mapped[Optional[str]] = mapped_column(String(50))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50))

    # Project info
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    project_name: Mapped[str] = mapped_column(String(255))
    project_status: Mapped[str] = mapped_column(String(100))

    # Organization
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Media file info
    media_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    filename: Mapped[Optional[str]] = mapped_column(String(1024))
    filemime: Mapped[Optional[str]] = mapped_column(String(256))
    fspath: Mapped[Optional[str]] = mapped_column(String(1024))
    cdn_url: Mapped[Optional[str]] = mapped_column(String(1024))
    file_length: Mapped[Optional[int]] = mapped_column(Integer)

    # Creator info (JSONB)
    created_by: Mapped[dict] = mapped_column(JSONB)
    # Structure: {id: UUID, name: str, avatar: UUID}

    # Participants (JSON array)
    participants: Mapped[List[dict]] = mapped_column(JSONB)
    # Structure: [{id: UUID, name: str, avatar: UUID, role: str}]

    participant_count: Mapped[int] = mapped_column(Integer)

    # Activity timestamp
    activity: Mapped[datetime] = mapped_column(DateTime(timezone=True))
