"""Category ORM model.

Second structural level within a realm. The `realm_id` column is denormalized
from shelf for fast realm-scoped filtering.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Category(TableBase):
    """Level-2 container within a shelf (code: A01, A02 ...)."""

    __tablename__ = "category"
    __table_args__ = (
        Index(
            "ix_category_realm_id",
            "realm_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "ix_category_shelf_id",
            "shelf_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "uq_category_shelf_code_active",
            "shelf_id",
            "code",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "uq_category_shelf_name_active",
            "shelf_id",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    shelf_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
