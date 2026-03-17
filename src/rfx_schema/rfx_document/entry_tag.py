"""
EntryTag ORM Model
==================

Junction table linking entries to tags (M:N). No audit columns — the relationship
is created or deleted atomically, never partially updated.

Primary key: composite (entry_id, tag_id).
Extra index: tag_id — allows efficient lookups of all entries for a given tag.
"""

from __future__ import annotations

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA


class EntryTag(Base):
    """M:N junction between Entry and Tag. No audit trail."""

    __tablename__ = "entry_tag"
    __table_args__ = (
        Index("ix_entry_tag_tag_id", "tag_id"),
        {"schema": SCHEMA},
    )

    entry_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tag_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)