from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA

if TYPE_CHECKING:
    from .message import Message


class MessageEmbedded(TableBase):
    """Embedded widgets or content previews."""

    __tablename__ = "message_embedded"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    type: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    host: Mapped[Optional[str]] = mapped_column(String(1024))
    endpoint: Mapped[Optional[str]] = mapped_column(String(1024))
    options: Mapped[dict] = mapped_column(JSONB, default=dict)

    message: Mapped["Message"] = relationship(back_populates="embeds")
