"""
Tag ORM Model
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Index, String, UUID, text
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Tag(TableBase):
    """Reusable label that can be attached to any entry."""

    __tablename__ = "tag"
    __table_args__ = (
        Index(
            "uq_tag_realm_name_active",
            "realm_id",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index("ix_tag_name", "name"),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
