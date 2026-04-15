"""Tag ORM model."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Tag(TableBase):
    """Reusable global label that can be attached to any entry."""

    __tablename__ = "tag"
    __table_args__ = (
        Index(
            "uq_tag_name_active",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        Index("ix_tag_name", "name"),
        {"schema": SCHEMA},
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
