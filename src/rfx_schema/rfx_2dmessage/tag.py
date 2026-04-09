"""
Message Service ORM Mapping (Schema Layer)
==========================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``src/rfx_message/model.py``. These models are used for Alembic autogenerate
and lightweight metadata introspection without importing the full message
service stack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
import uuid

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from fluvius.data import UUID_TYPE
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    from .message import Message
    pass


class MessageTag(TableBase):
    __tablename__ = "message_tag"
    __table_args__ = {"schema": SCHEMA}

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), primary_key=True
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.tag._id"), primary_key=True
    )

    # message = relationship("Message", back_populates="message_tags")
    # tag = relationship("Tag", back_populates="message_tags")

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

    # messages: Mapped[List["Message"]] = relationship(
    #     "Message",
    #     secondary=f"{SCHEMA}.message_tag",
    #     back_populates="tags",
    #     viewonly=True
    # )

    # message_tags = relationship("MessageTag", back_populates="tag")

    __table_args__ = (
        UniqueConstraint(
            "profile_id", "key", "_deleted", name="idx_tag_profile_id_key_deleted"
        ),
        {"schema": SCHEMA},
    )




