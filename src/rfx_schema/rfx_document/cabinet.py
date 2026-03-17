"""
Cabinet ORM Model
=================

Third structural level — the document container. Code pattern: {CategoryCode}-{suffix}
e.g. "A01-001". realm_id is denormalized for fast realm-scoped queries.

Unique constraint: (realm_id, category_id, code) — code unique within a category scope.
Indexes: realm_id, category_id.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Cabinet(TableBase):
    """Level-3 document container (code: A01-001, A01-002 ...)."""

    __tablename__ = "cabinet"
    __table_args__ = (
        UniqueConstraint("realm_id", "category_id", "code", name="uq_cabinet_realm_category_code"),
        Index("ix_cabinet_realm_id",    "realm_id"),
        Index("ix_cabinet_category_id", "category_id"),
        {"schema": SCHEMA},
    )

    realm_id:    Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    category_id: Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    code:        Mapped[str]         = mapped_column(String(20),   nullable=False)
    name:        Mapped[str]         = mapped_column(String(255),  nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)