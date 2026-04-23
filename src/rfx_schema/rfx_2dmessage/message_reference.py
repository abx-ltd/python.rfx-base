from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA

if TYPE_CHECKING:
    from .message import Message


class MessageReference(TableBase):
    """External resources linked to the message."""

    __tablename__ = "message_reference"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    description: Mapped[Optional[str]] = mapped_column(String(1024))
    favorited: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    kind: Mapped[Optional[str]] = mapped_column(String(1024))
    resource: Mapped[Optional[str]] = mapped_column(String(1024))
    source: Mapped[Optional[str]] = mapped_column(String(1024))
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    title: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__email: Mapped[Optional[str]] = mapped_column(String(255))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(12))

    message: Mapped["Message"] = relationship(back_populates="references")
