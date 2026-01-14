from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA

if TYPE_CHECKING:
    from .message import Message


class MessageAttachment(TableBase):
    """Files linked to a message."""

    __tablename__ = "message_attachment"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), primary_key=True
    )
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    message: Mapped["Message"] = relationship(back_populates="attachments")
