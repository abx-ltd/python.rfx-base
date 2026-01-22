"""
Message Service ORM Mapping (Schema Layer)
==========================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``src/rfx_message/model.py``. These models are used for Alembic autogenerate
and lightweight metadata introspection without importing the full message
service stack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from fluvius.data import UUID_TYPE
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    pass


class Tag(TableBase):
    """Global tags for message classification."""

    __tablename__ = "tag"
    __table_args__ = {"schema": SCHEMA}

    key: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    font_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_id: Mapped[Optional[UUID_TYPE]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Ensure (profile_id, key) is unique per profile; the name is the constraint name,
    # not a column name.
    __table_args__ = (
        UniqueConstraint("profile_id", "key", name="idx_tag_profile_id_key"),
        {"schema": SCHEMA},
    )
