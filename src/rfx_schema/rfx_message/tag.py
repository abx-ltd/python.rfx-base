"""
Message Service ORM Mapping (Schema Layer)
==========================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``src/rfx_message/model.py``. These models are used for Alembic autogenerate
and lightweight metadata introspection without importing the full message
service stack.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    Enum as SQLEnum,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import (
    TagGroupEnum,
)


class Tag(TableBase):
    """Global tags for message classification."""

    __tablename__ = "tag"
    __table_args__ = {"schema": SCHEMA}

    name: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7))
    font_color: Mapped[Optional[str]] = mapped_column(String(7))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    group: Mapped[Optional[TagGroupEnum]] = mapped_column(
        SQLEnum(TagGroupEnum, name="taggroupenum", schema=SCHEMA)
    )


class TagPreference(TableBase):
    """User preferences for how tags behave or render."""

    __tablename__ = "tag_preference"

    option: Mapped[dict] = mapped_column(JSONB, default=dict)
