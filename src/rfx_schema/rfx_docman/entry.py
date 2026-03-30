"""
Entry ORM Model
===============

Files and folders within a cabinet. Uses `type` discriminator (EntryType enum) to
distinguish between file types. Folder rows are optional — only created when metadata
(tags, description, etc.) must be stored explicitly.

Unique constraint: (cabinet_id, path) — path unique within cabinet.
Indexes: cabinet_id, type.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import BigInteger, Enum as SQLEnum, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import EntryTypeEnum


class Entry(TableBase):
    """A file or folder within a cabinet."""

    __tablename__ = "entry"
    __table_args__ = (
        Index(
            "uq_entry_cabinet_id_path_active",
            "cabinet_id",
            "path",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_entry_cabinet_path_prefix",
            "cabinet_id",
            "path",
            postgresql_ops={"path": "text_pattern_ops"},
            postgresql_where=text("_deleted IS NULL"),
        ),
        # Filter by type in cabinet (upsert FOLDER row, list by type...)
        Index(
            "ix_entry_cabinet_type",
            "cabinet_id",
            "type",
            postgresql_where=text("_deleted IS NULL"),
        ),
        # Search by name in cabinet
        Index(
            "ix_entry_cabinet_name",
            "cabinet_id",
            "name",
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[EntryTypeEnum] = mapped_column(
        SQLEnum(EntryTypeEnum, name="entrytypeenum", schema=SCHEMA), nullable=False
    )
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)