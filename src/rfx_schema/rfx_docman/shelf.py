"""
Shelf ORM Model
===============

First structural level within a realm. Identified by a single-letter code (A–Z).

Unique constraint: (realm_id, code) — code unique within a realm.
Index: realm_id — fast listing of shelves per realm.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String,text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Shelf(TableBase):
    """Level-1 container within a realm (code: A, B, C ...)."""

    __tablename__ = "shelf"
    __table_args__ = (
        Index("ix_shelf_realm_id", "realm_id"),
        Index(
            "uq_shelf_realm_code_active",
            "realm_id",
            "code",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    realm_id:    Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    code:        Mapped[str]         = mapped_column(String(10),   nullable=False)
    name:        Mapped[str]         = mapped_column(String(255),  nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
