"""Comment System ORM Models (Schema Layer)"""

from __future__ import annotations
from typing import Optional
import uuid

import sqlalchemy as sa
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Comment(TableBase):
    """Comments stored in ``rfx_client.comment``."""

    __tablename__ = "comment"
    __table_args__ = (
        sa.Index("idx_comment_depth", "depth"),
        sa.Index("idx_comment_master", "master_id"),
        sa.Index("idx_comment_parent", "parent_id"),
        {"schema": SCHEMA},
    )

    master_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.comment._id", name="comment_parent_id_fkey", ondelete="CASCADE"
        ),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    source: Mapped[Optional[str]] = mapped_column(String)


class CommentReaction(TableBase):
    """Comment reactions in ``rfx_client.comment_reaction``."""

    __tablename__ = "comment_reaction"
    __table_args__ = (
        sa.UniqueConstraint(
            "comment_id", "user_id", "reaction_type", name="uq_comment_reaction"
        ),
        sa.Index("idx_comment_reaction_comment", "comment_id"),
        sa.Index("idx_comment_reaction_user", "user_id"),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.comment._id",
            name="comment_reaction_comment_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(50), nullable=False)


class CommentAttachment(TableBase):
    """Comment attachments in ``rfx_client.comment_attachment``."""

    __tablename__ = "comment_attachment"
    __table_args__ = (
        sa.UniqueConstraint("comment_id", "media_entry_id", name="uq_comment_media"),
        sa.Index(
            "idx_attachment_comment",
            "comment_id",
            postgresql_where=sa.text("_deleted IS NULL"),
        ),
        sa.Index(
            "idx_attachment_media",
            "media_entry_id",
            postgresql_where=sa.text("_deleted IS NULL"),
        ),
        sa.Index(
            "idx_attachment_primary",
            "comment_id",
            "is_primary",
            postgresql_where=sa.text("(_deleted IS NULL) AND (is_primary = true)"),
        ),
        {"schema": SCHEMA},
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comment._id", name="fk_comment", ondelete="CASCADE"),
        nullable=False,
    )
    media_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey(
        #     '"cpo-media"."media-entry"._id', 
        #     name="fk_media",
        #     ondelete="RESTRICT",
        # ),
        nullable=False,
    )
    attachment_type: Mapped[Optional[str]] = mapped_column(String(50))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)


class CommentIntegration(TableBase):
    """Comment integration in ``rfx_client.comment_integration``."""

    __tablename__ = "comment_integration"
    __table_args__ = {"schema": SCHEMA}

    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String)
