"""Shelf ORM model.

First structural level within a realm, identified by a short code.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Shelf(TableBase):
    """Level-1 container within a realm (code: A, B, C ...)."""

    __tablename__ = "shelf"
    __table_args__ = (
        Index(
            "uq_shelf_realm_code_active",
            "realm_id",
            "code",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index(
            "idx_shelf_realm_active",
            "realm_id",
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
