# models/entry.py
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from rfx_schema.rfx_media.media import MediaEntry

from . import SCHEMA, TableBase
from .types import EntryTypeEnum, EntryStatusEnum


class Entry(TableBase):
    """
    A file or folder within a cabinet.

    Hierarchy traversal  → EntryAncestor (closure table)
    path / parent_path   → display only, dùng cho Frontend breadcrumb
    """

    __tablename__ = "entry"
    __table_args__ = (
        # ── Uniqueness ───────────────────────────────────────────────────
        Index(
            "uq_entry_cabinet_path_active",
            "cabinet_id",
            "path",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "uq_entry_cabinet_parent_name_active",
            "cabinet_id",
            "parent_path",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        # ── Lookup indexes ───────────────────────────────────────────────
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
        Index(
            "ix_entry_media_entry_id",
            "media_entry_id",
            postgresql_where=text("media_entry_id IS NOT NULL AND _deleted IS NULL"),
        ),
        # ── Constraints ──────────────────────────────────────────────────
        CheckConstraint(
            "(type = 'FOLDER' AND media_entry_id IS NULL) OR"
            " (type != 'FOLDER' AND media_entry_id IS NOT NULL)",
            name="ck_entry_media_by_type",
        ),
        {"schema": SCHEMA},
    )

    cabinet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    parent_path: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Display only. Tree traversal dùng entry_ancestor.",
    )
    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    path: Mapped[str] = mapped_column(
        String(2561),
        Computed(
            "CASE WHEN parent_path = '' THEN name ELSE parent_path || '/' || name END",
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
    is_virtual: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    status: Mapped[EntryStatusEnum] = mapped_column(
        SQLEnum(EntryStatusEnum, name="entrystatusenum", schema=SCHEMA),
        nullable=False,
        default=EntryStatusEnum.PENDING,
    )
