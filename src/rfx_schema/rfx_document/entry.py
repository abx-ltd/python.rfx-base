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

from typing import Optional

from sqlalchemy import BigInteger, Enum as SQLEnum, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import EntryTypeEnum


class Entry(TableBase):
    """A file or folder within a cabinet."""

    __tablename__ = "entry"
    __table_args__ = (
        UniqueConstraint("cabinet_id", "path", name="uq_entry_cabinet_id_path"),
        Index("ix_entry_cabinet_id", "cabinet_id"),
        Index("ix_entry_type",       "type"),
        Index("ix_entry_name",       "name"),
        {"schema": SCHEMA},
    )

    cabinet_id: Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    path:       Mapped[str]         = mapped_column(String(2048), nullable=False)
    name:       Mapped[str]         = mapped_column(String(512),  nullable=False)
    type:       Mapped[EntryTypeEnum]   = mapped_column(
        SQLEnum(EntryTypeEnum, name="entrytypeenum", schema=SCHEMA), nullable=False
    )
    size:       Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)