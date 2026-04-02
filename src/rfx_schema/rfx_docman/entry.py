"""
Entry ORM Model
===============

Files and folders within a cabinet. Uses `type` discriminator (EntryType enum) to
distinguish between file types. Folder rows are optional - only created when metadata
(tags, description, etc.) must be stored explicitly.

Unique constraint: (cabinet_id, path) - path unique within cabinet.
Indexes: cabinet_id, type.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Computed, Enum as SQLEnum, ForeignKey, Index, String, text , CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from rfx_schema.rfx_media.media import MediaEntry

from . import SCHEMA, TableBase
from .types import EntryTypeEnum, EntryStatusEnum


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
            "uq_entry_cabinet_id_parent_path__name_active",
            "cabinet_id",
            "parent_path",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_entry_cabinet_parent_path",
            "cabinet_id",
            "parent_path",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_entry_cabinet_path_prefix",
            "cabinet_id",
            "path",
            postgresql_ops={"path": "text_pattern_ops"},
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_entry_cabinet_type",
            "cabinet_id",
            "type",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_entry_cabinet_name",
            "cabinet_id",
            "name",
            postgresql_where=text("_deleted IS NULL"),
        ),
        CheckConstraint(
            "(type = 'FOLDER' AND media_entry_id IS NULL) OR "
            "(type != 'FOLDER' AND media_entry_id IS NOT NULL)",
            name="ck_entry_media_by_type",
        ),
        {"schema": SCHEMA},
    )

    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)

    # Generated column from parent_path + name.
    path: Mapped[str] = mapped_column(
        String(2048),
        Computed(
            "CASE WHEN parent_path = '' THEN name "
            "ELSE parent_path || '/' || name END",
            persisted=True,
        ),
    )
    type: Mapped[EntryTypeEnum] = mapped_column(
        SQLEnum(EntryTypeEnum, name="entrytypeenum", schema=SCHEMA),
        nullable=False,
    )

    media_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(MediaEntry._id, name="fk_entry_media", ondelete="RESTRICT"),
        nullable=True,
    )

    status: Mapped[EntryStatusEnum] = mapped_column(
        SQLEnum(EntryStatusEnum, name="entrystatusenum", schema=SCHEMA),
        nullable=False,
        default=EntryStatusEnum.PENDING,
    )