from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA
from .types import (
    BoxTypeEnum,
    ContentTypeEnum,
    DirectionTypeEnum,
    MessageCategoryEnum,
    MessageTypeEnum,
    PriorityLevelEnum,
)


class MessageBoxView(Base):
    """
    ORM mapping for the `_message_box` view defined via PGView.
    Exposes a flattened dataset that joins messages and recipients to
    support notification fan-out without additional joins.
    """

    __tablename__ = "_message_box"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    recipient_id: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    subject: Mapped[Optional[str]] = mapped_column(String(1024))
    content: Mapped[Optional[str]] = mapped_column(String(1024))
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )
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

    # Recipient status fields
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean)
    recipient_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Box fields
    box_key: Mapped[Optional[str]] = mapped_column(String(1024))
    box_name: Mapped[Optional[str]] = mapped_column(String(1024))
    box_type_enum: Mapped[Optional[BoxTypeEnum]] = mapped_column(
        SQLEnum(BoxTypeEnum, name="boxtypeenum", schema=SCHEMA)
    )

    # Target and aggregation fields
    target_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    message_count: Mapped[Optional[int]] = mapped_column(Integer)
    root_type: Mapped[str] = mapped_column(String)
    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA)
    )

    def __repr__(self) -> str:
        return (
            f"<MessageBoxView(message_id={self.message_id}, "
            f"sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
        )


class MessageThreadView(Base):
    """
    ORM mapping for the `_message_thread` view defined via PGView.
    Exposes thread-level aggregated message data with sender/recipient profiles
    and trashed status information.
    """

    __tablename__ = "_message_thread"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Profile information
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    recipient_id: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)

    # Message content fields
    subject: Mapped[Optional[str]] = mapped_column(String(1024))
    content: Mapped[Optional[str]] = mapped_column(String(1024))
    rendered_content: Mapped[Optional[str]] = mapped_column(String(1024))
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )
    is_important: Mapped[Optional[bool]] = mapped_column(Boolean)
    expirable: Mapped[Optional[bool]] = mapped_column(Boolean)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    request_read_receipt: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Message metadata
    priority: Mapped[Optional[PriorityLevelEnum]] = mapped_column(
        SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA)
    )
    message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )
    delivery_status: Mapped[Optional[str]] = mapped_column(String(1024))
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    context: Mapped[Optional[dict]] = mapped_column(JSON)

    # Template fields
    template_key: Mapped[Optional[str]] = mapped_column(String(1024))
    template_version: Mapped[Optional[int]] = mapped_column(Integer)
    template_locale: Mapped[Optional[str]] = mapped_column(String(1024))
    template_engine: Mapped[Optional[str]] = mapped_column(String(1024))
    template_data: Mapped[Optional[dict]] = mapped_column(JSON)
    render_strategy: Mapped[Optional[str]] = mapped_column(String(1024))
    render_status: Mapped[Optional[str]] = mapped_column(String(1024))
    rendered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    render_error: Mapped[Optional[str]] = mapped_column(String(1024))

    # Aggregation fields
    message_count: Mapped[Optional[int]] = mapped_column(Integer)
    visible_profile_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True))
    )

    def __repr__(self) -> str:
        return (
            f"<MessageThreadView(message_id={self.message_id}, "
            f"thread_id={self.thread_id})>"
        )
