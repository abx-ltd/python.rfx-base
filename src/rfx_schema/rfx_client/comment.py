"""
Comment System ORM Models (Schema Layer)
========================================
Note: Comments are stored in rfx_client schema in current database
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA


class Comment(TableBase):
    """Comments stored in ``rfx_client.comment``."""

    __tablename__ = "comment"

    master_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE")
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    source: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    parent: Mapped[Optional["Comment"]] = relationship(
        back_populates="replies", remote_side="_id"
    )
    replies: Mapped[List["Comment"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    reactions: Mapped[List["CommentReaction"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["CommentAttachment"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )
    integrations: Mapped[List["CommentIntegration"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class CommentReaction(TableBase):
    """Comment reactions in ``rfx_client.comment_reaction``."""

    __tablename__ = "comment_reaction"
    __table_args__ = (
        UniqueConstraint(
            "comment_id", "user_id", "reaction_type", name="uq_comment_reaction"
        ),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="reactions")


class CommentAttachment(TableBase):
    """Comment attachments in ``rfx_client.comment_attachment``."""

    __tablename__ = "comment_attachment"
    __table_args__ = (
        UniqueConstraint("comment_id", "media_entry_id", name="uq_comment_media"),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", ondelete="CASCADE"),
        nullable=False,
    )
    media_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    attachment_type: Mapped[Optional[str]] = mapped_column(String(50))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="attachments")


class CommentIntegration(TableBase):
    """Comment integration tracking in ``rfx_client.comment_integration``."""

    __tablename__ = "comment_integration"

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="integrations")
