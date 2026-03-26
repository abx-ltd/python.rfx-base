"""
Tag ORM Model
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, UUID , UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


from . import TableBase, SCHEMA


class Tag(TableBase):
    """Reusable label that can be attached to any entry."""

    __tablename__ = "tag"
    __table_args__ = (
        UniqueConstraint("realm_id","name", name="uq_tag_realm_name"),
        Index("ix_tag_name", "name"),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    name:  Mapped[str]         = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    icon:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)