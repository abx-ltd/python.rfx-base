"""
RFX Discuss View Mappings
==========================
ORM models for discussion system views.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


# ============================================================================
# COMMENT VIEWS
# ============================================================================


class CommentView(TableBase):
    """
    View: _comment
    Comments with creator info and aggregate counts.
    """

    __tablename__ = "_comment"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # Thread hierarchy
    master_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    depth: Mapped[int] = mapped_column(Integer)

    # Content
    content: Mapped[str] = mapped_column(Text)

    # Context
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Creator info (JSONB)
    creator: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    # Aggregate counts
    attachment_count: Mapped[int] = mapped_column(Integer)
    reaction_count: Mapped[int] = mapped_column(Integer)
    flag_count: Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return (
            f"<CommentView(id={self._id}, depth={self.depth}, "
            f"attachments={self.attachment_count}, "
            f"reactions={self.reaction_count})>"
        )


class CommentAttachmentView(TableBase):
    """
    View: _comment_attachment
    Comment attachments with media metadata and uploader info.
    """

    __tablename__ = "_comment_attachment"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    media_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Attachment metadata
    attachment_type: Mapped[Optional[str]] = mapped_column(String(50))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean)

    # Media file info (from media-entry table)
    filename: Mapped[Optional[str]] = mapped_column(String)
    filehash: Mapped[Optional[str]] = mapped_column(String)
    filemime: Mapped[Optional[str]] = mapped_column(String)
    length: Mapped[Optional[int]] = mapped_column(Integer)
    fspath: Mapped[Optional[str]] = mapped_column(String)
    fskey: Mapped[Optional[str]] = mapped_column(String)
    compress: Mapped[Optional[bool]] = mapped_column(Boolean)
    cdn_url: Mapped[Optional[str]] = mapped_column(String)
    resource: Mapped[Optional[str]] = mapped_column(String)
    resource__id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Uploader info (JSONB)
    uploader: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentAttachmentView(id={self._id}, "
            f"comment_id={self.comment_id}, "
            f"filename={self.filename})>"
        )


class CommentReactionView(TableBase):
    """
    View: _comment_reaction
    Individual comment reactions with reactor info.
    """

    __tablename__ = "_comment_reaction"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reaction_type: Mapped[str] = mapped_column(String(50))

    # Reactor info (JSONB)
    reactor: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentReactionView(id={self._id}, "
            f"comment_id={self.comment_id}, "
            f"type={self.reaction_type})>"
        )


class CommentReactionSummaryView(TableBase):
    """
    View: _comment_reaction_summary
    Aggregated reaction counts by type with user lists.
    """

    __tablename__ = "_comment_reaction_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reaction_type: Mapped[str] = mapped_column(String(50))
    reaction_count: Mapped[int] = mapped_column(Integer)

    # Array of user objects (JSONB)
    users: Mapped[list] = mapped_column(
        JSONB, comment="Array of {id, name, avatar} objects"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentReactionSummaryView(comment_id={self.comment_id}, "
            f"type={self.reaction_type}, count={self.reaction_count})>"
        )


# ============================================================================
# FLAG VIEWS
# ============================================================================


class CommentFlagView(TableBase):
    """
    View: _comment_flag
    Comment flags with reporter info and comment preview.
    """

    __tablename__ = "_comment_flag"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reported_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Reporter info (JSONB)
    reporter: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    # Comment preview (JSONB)
    comment_preview: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, content (first 200 chars), creator}"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentFlagView(id={self._id}, "
            f"comment_id={self.comment_id}, "
            f"reason={self.reason}, status={self.status})>"
        )


class CommentFlagResolutionView(TableBase):
    """
    View: _comment_flag_resolution
    Flag resolutions with resolver and original flag info.
    """

    __tablename__ = "_comment_flag_resolution"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    flag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    resolved_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[Optional[str]] = mapped_column(Text)
    resolution_action: Mapped[Optional[str]] = mapped_column(String(50))

    # Resolver info (JSONB)
    resolver: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    # Original flag info (JSONB)
    flag_info: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, comment_id, reason, status, reported_by}"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentFlagResolutionView(id={self._id}, "
            f"flag_id={self.flag_id}, "
            f"action={self.resolution_action})>"
        )


class CommentFlagSummaryView(TableBase):
    """
    View: _comment_flag_summary
    Aggregated flag statistics per comment.
    """

    __tablename__ = "_comment_flag_summary"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Flag counts by status
    total_flags: Mapped[int] = mapped_column(Integer)
    pending_flags: Mapped[int] = mapped_column(Integer)
    resolved_flags: Mapped[int] = mapped_column(Integer)
    rejected_flags: Mapped[int] = mapped_column(Integer)

    # Flag reasons breakdown (JSONB)
    flag_reasons: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Object mapping reason -> count"
    )

    latest_flag_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<CommentFlagSummaryView(comment_id={self.comment_id}, "
            f"total={self.total_flags}, pending={self.pending_flags})>"
        )


# ============================================================================
# SUBSCRIPTION VIEW
# ============================================================================


class CommentSubscriptionView(TableBase):
    """
    View: _comment_subscription
    User subscriptions to comment threads with subscriber info.
    """

    __tablename__ = "_comment_subscription"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(Boolean)

    # Comment context
    comment_content: Mapped[str] = mapped_column(Text)
    comment_creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Subscriber info (JSONB)
    subscriber: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Contains: {id, name, avatar}"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentSubscriptionView(id={self._id}, "
            f"comment_id={self.comment_id}, "
            f"user_id={self.user_id}, active={self.is_active})>"
        )


__all__ = [
    "CommentView",
    "CommentAttachmentView",
    "CommentReactionView",
    "CommentReactionSummaryView",
    "CommentFlagView",
    "CommentFlagResolutionView",
    "CommentFlagSummaryView",
    "CommentSubscriptionView",
]
