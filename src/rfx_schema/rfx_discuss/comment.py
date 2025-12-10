"""
RFX Discuss Comment Models
===========================
Core comment and discussion tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import TableBase, SCHEMA


# ============================================================================
# CORE COMMENT TABLE
# ============================================================================


class Comment(TableBase):
    """
    Main comment table supporting threaded discussions.
    """

    __tablename__ = "comment"
    __table_args__ = (
        Index("idx_comment_master", "master_id"),
        Index("idx_comment_parent", "parent_id"),
        Index("idx_comment_depth", "depth"),
        Index("ix_comment_resource_resource_id", "resource", "resource_id"),
        {"schema": SCHEMA},
    )

    # Thread hierarchy
    master_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE"),
        nullable=True,
    )
    depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Context
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    resource: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Relationships
    children: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id],
    )
    parent: Mapped[Optional[Comment]] = relationship(
        "Comment",
        back_populates="children",
        remote_side="Comment._id",  # ← FIX: String reference thay vì "_id"
        foreign_keys=[parent_id],
    )

    attachments: Mapped[list[CommentAttachment]] = relationship(
        "CommentAttachment",
        back_populates="comment",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[list[CommentReaction]] = relationship(
        "CommentReaction",
        back_populates="comment",
        cascade="all, delete-orphan",
    )
    flags: Mapped[list[CommentFlag]] = relationship(
        "CommentFlag",
        back_populates="comment",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list[CommentSubscription]] = relationship(
        "CommentSubscription",
        back_populates="comment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Comment(id={self._id}, depth={self.depth}, "
            f"content='{self.content[:50]}...')>"
        )


# ============================================================================
# COMMENT ATTACHMENTS
# ============================================================================


class CommentAttachment(TableBase):
    """
    Media attachments for comments (images, videos, documents).
    Links to media-entry table in cpo-media schema.
    """

    from ..rfx_media.media import MediaEntry

    __tablename__ = "comment_attachment"
    __table_args__ = (
        UniqueConstraint(
            "comment_id",
            "media_entry_id",
            name="uq_comment_media",
        ),
        Index(
            "idx_attachment_comment",
            "comment_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "idx_attachment_media",
            "media_entry_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "idx_attachment_primary",
            "comment_id",
            "is_primary",
            postgresql_where=text("_deleted IS NULL AND is_primary = true"),
        ),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE", name="fk_comment"),
        nullable=False,
    )

    media_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(MediaEntry._id, name="fk_media", ondelete="RESTRICT"),
        nullable=False,
    )

    attachment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    caption: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Fixed: Match DDL exactly - nullable=True, server_default
    display_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        server_default=text("0"),
    )
    is_primary: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default=text("false"),
    )

    # Relationships
    comment: Mapped[Comment] = relationship("Comment", back_populates="attachments")

    def __repr__(self) -> str:
        return (
            f"<CommentAttachment(id={self._id}, comment_id={self.comment_id}, "
            f"type={self.attachment_type})>"
        )


# ============================================================================
# COMMENT REACTIONS
# ============================================================================


class CommentReaction(TableBase):
    """
    User reactions to comments (like, love, etc.).
    """

    __tablename__ = "comment_reaction"
    __table_args__ = (
        UniqueConstraint(
            "comment_id",
            "user_id",
            "reaction_type",
            name="uq_comment_reaction",
        ),
        Index("idx_comment_reaction_comment", "comment_id"),
        Index("idx_comment_reaction_user", "user_id"),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    reaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Relationships
    comment: Mapped[Comment] = relationship("Comment", back_populates="reactions")

    def __repr__(self) -> str:
        return (
            f"<CommentReaction(id={self._id}, comment_id={self.comment_id}, "
            f"type={self.reaction_type})>"
        )


# ============================================================================
# COMMENT FLAGS (REPORTING)
# ============================================================================


class CommentFlag(TableBase):
    """
    User-reported flags for inappropriate comments.
    """

    __tablename__ = "comment_flag"
    __table_args__ = (
        Index("idx_comment_flag_comment", "comment_id"),
        Index("idx_comment_flag_reporter", "reported_by_user_id"),
        Index("idx_comment_flag_status", "status"),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE"),
        nullable=False,
    )
    reported_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'pending'::character varying"),
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    comment: Mapped[Comment] = relationship("Comment", back_populates="flags")
    resolution: Mapped[Optional[CommentFlagResolution]] = relationship(
        "CommentFlagResolution",
        back_populates="flag",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<CommentFlag(id={self._id}, comment_id={self.comment_id}, "
            f"reason={self.reason}, status={self.status})>"
        )


# ============================================================================
# FLAG RESOLUTIONS
# ============================================================================


class CommentFlagResolution(TableBase):
    """
    Resolution records for comment flags.
    """

    __tablename__ = "comment_flag_resolution"
    __table_args__ = (
        UniqueConstraint("flag_id", name="comment_flag_resolution_flag_id_key"),
        Index(
            "idx_flag_resolution_flag_id",
            "flag_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "idx_flag_resolution_resolver",
            "resolved_by_user_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment_flag._id", ondelete="CASCADE", name="fk_flag"),
        nullable=False,
        unique=True,
    )
    resolved_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    # Fixed: Match DDL - nullable=False with server_default
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    resolution_action: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationships
    flag: Mapped[CommentFlag] = relationship(
        "CommentFlag",
        back_populates="resolution",
    )

    def __repr__(self) -> str:
        return (
            f"<CommentFlagResolution(id={self._id}, flag_id={self.flag_id}, "
            f"action={self.resolution_action})>"
        )


# ============================================================================
# COMMENT SUBSCRIPTIONS
# ============================================================================


class CommentSubscription(TableBase):
    """
    User subscriptions to comment threads for notifications.
    """

    from ..rfx_user.profile import Profile

    __tablename__ = "comment_subscription"
    __table_args__ = (
        UniqueConstraint(
            "comment_id",
            "user_id",
            name="uq_comment_user",
        ),
        Index(
            "idx_subscription_comment",
            "comment_id",
            postgresql_where=text("_deleted IS NULL AND is_active = true"),
        ),
        Index(
            "idx_subscription_user",
            "user_id",
            postgresql_where=text("_deleted IS NULL AND is_active = true"),
        ),
        Index(
            "idx_subscription_active",
            "is_active",
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE", name="fk_comment"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(Profile._id, ondelete="CASCADE", name="fk_user"),
        nullable=False,
    )
    # Fixed: Match DDL - nullable=True with server_default
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default=text("true"),
    )

    # Relationships
    comment: Mapped[Comment] = relationship("Comment", back_populates="subscriptions")

    def __repr__(self) -> str:
        return (
            f"<CommentSubscription(id={self._id}, comment_id={self.comment_id}, "
            f"user_id={self.user_id}, active={self.is_active})>"
        )


# ============================================================================
# COMMENT INTEGRATION (External Systems)
# ============================================================================


class CommentIntegration(TableBase):
    """
    Links comments to external systems (Jira, GitHub, etc.).
    """

    __tablename__ = "comment_integration"
    __table_args__ = {"schema": SCHEMA}

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<CommentIntegration(id={self._id}, provider={self.provider}, "
            f"external_id={self.external_id})>"
        )


__all__ = [
    "Comment",
    "CommentAttachment",
    "CommentReaction",
    "CommentFlag",
    "CommentFlagResolution",
    "CommentSubscription",
    "CommentIntegration",
]
