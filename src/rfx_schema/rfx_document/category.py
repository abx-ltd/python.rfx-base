"""
Category ORM Model
==================

Second structural level within a realm. Code pattern: {ShelfCode}{2-digit serial}
e.g. "A01", "A02", "B01".

realm_id is denormalized here (copied from shelf) to enable fast realm-scoped queries
without a join to shelf.

Unique constraint: (realm_id, shelf_id, code) — code unique within a shelf scope.
Indexes: realm_id, shelf_id.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Category(TableBase):
    """Level-2 container within a shelf (code: A01, A02 ...)."""

    __tablename__ = "category"
    __table_args__ = (
        UniqueConstraint("realm_id", "shelf_id", "code", name="uq_category_realm_shelf_code"),
        Index("ix_category_realm_id", "realm_id"),
        Index("ix_category_shelf_id", "shelf_id"),
        {"schema": SCHEMA},
    )

    realm_id:    Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    shelf_id:    Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    code:        Mapped[str]         = mapped_column(String(10),   nullable=False)
    name:        Mapped[str]         = mapped_column(String(255),  nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)