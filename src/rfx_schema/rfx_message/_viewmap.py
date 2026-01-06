from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA
from .types import (
    ContentTypeEnum,
    MessageCategoryEnum,
    MessageTypeEnum,
    PriorityLevelEnum,
)


class MessageRecipientsView(Base):
    """
    ORM mapping for the `_message_recipient` view defined via PGView.
    Exposes a flattened dataset that joins messages and recipients to
    support notification fan-out without additional joins.
    """

    __tablename__ = "_message_recipient"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    subject: Mapped[Optional[str]] = mapped_column(String(1024))
    content: Mapped[Optional[str]] = mapped_column(String(1024))
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )

    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    expirable: Mapped[Optional[bool]] = mapped_column(Boolean)
    priority: Mapped[Optional[PriorityLevelEnum]] = mapped_column(
        SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA)
    )
    message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )
    category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
        SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    )
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return (
            f"<MessageRecipientsView(record_id={self.record_id}, "
            f"message_id={self.message_id}, recipient_id={self.recipient_id})>"
        )
