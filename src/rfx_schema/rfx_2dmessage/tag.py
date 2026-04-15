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
    Index,
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
    __table_args__ = (Index("idx_message_tag_tag_id", "tag_id"),
                    {"schema": SCHEMA},)

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id", ondelete="CASCADE"), primary_key=True
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.tag._id", ondelete="CASCADE"), primary_key=True
    )


    # message = relationship("Message", back_populates="message_tags")
    # tag = relationship("Tag", back_populates="message_tags")

class Tag(TableBase):
    """Global tags for message classification."""

    __tablename__ = "tag"
    __table_args__ = (
            Index("uq_tag_mailbox_key_deleted","mailbox_id","key","_deleted",unique=True),
            {"schema": SCHEMA}
    )
    key: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    font_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mailbox_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.mailbox._id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )





