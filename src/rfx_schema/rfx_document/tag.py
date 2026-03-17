"""
Tag ORM Model
=============

Globally-scoped reusable tags. Tags are NOT scoped per realm — they are shared
across the entire document system and applied to entries via the entry_tag junction.

Unique constraint: name — tag name is globally unique.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


from . import TableBase, SCHEMA


class Tag(TableBase):
    """Reusable label that can be attached to any entry."""

    __tablename__ = "tag"
    __table_args__ = (
        Index("ix_tag_name", "name"),
        {"schema": SCHEMA},
    )

    name:  Mapped[str]         = mapped_column(String(255), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    icon:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)