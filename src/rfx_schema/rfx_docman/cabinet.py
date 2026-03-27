"""
Cabinet ORM Model
=================

Third structural level — the document container. Code pattern: {CategoryCode}-{suffix}
e.g. "A01-001". realm_id is denormalized for fast realm-scoped queries.

Unique constraint: (category_id, code) for active rows — code unique within a category scope.
Indexes: realm_id, category_id for active rows.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Cabinet(TableBase):
    """Level-3 document container (code: A01-001, A01-002 ...)."""

    __tablename__ = "cabinet"
    __table_args__ = (
        Index(
            "ix_cabinet_realm_id",
            "realm_id",
            postgresql_where=text(" _deleted IS NULL"),
        ),
        Index(
            "ix_cabinet_category_id",
            "category_id",
            postgresql_where=text(" _deleted IS NULL"),
        ),
        Index(
            "uq_cabinet_category_code_active",
            "category_id",
            "code",
            unique=True,
            postgresql_where=text(" _deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
