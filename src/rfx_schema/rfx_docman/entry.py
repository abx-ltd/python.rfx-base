# models/entry.py
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
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
from sqlalchemy.types import UserDefinedType

from rfx_schema.rfx_media.media import MediaEntry

from . import SCHEMA, TableBase
from .types import EntryTypeEnum, EntryStatusEnum


class LtreeType(UserDefinedType):
    """Lightweight ltree type for SQLAlchemy versions without built-in LTREE."""

    cache_ok = True

    def get_col_spec(self, **kw):
        return "LTREE"


class Entry(TableBase):
    """
    A file or folder within a cabinet.

    Virtual path hierarchy (S3-style):
      - Folder rows are optional. A prefix like "A/B/" is a valid
        parent_path even if no FOLDER row exists for "A/B".
      - `path` is a persisted computed column: never written directly.
      - Uniqueness is enforced by partial indexes on active rows (_deleted IS NULL).
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
            "idx_entry_ltree_gist",
            "path_ltree",
            postgresql_using="gist",
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
        Index(
            "ix_entry_media_entry_id",
            "media_entry_id",
            postgresql_where=text("media_entry_id IS NOT NULL AND _deleted IS NULL"),
        ),
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
    )
    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    # Persisted computed column — never set directly.
    # Formula: "" parent → name only; otherwise parent_path + "/" + name.
    path: Mapped[str] = mapped_column(
        String(2561),
        Computed(
            "CASE WHEN parent_path = '' THEN name ELSE parent_path || '/' || name END",
            persisted=True,
        ),
    )
    path_ltree: Mapped[str] = mapped_column(
        LtreeType(),
        Computed(
            f"\"{SCHEMA}\".path_text_to_ltree(CASE WHEN parent_path = '' THEN name ELSE parent_path || '/' || name END)",
            persisted=True,
        ),
        nullable=False,
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
