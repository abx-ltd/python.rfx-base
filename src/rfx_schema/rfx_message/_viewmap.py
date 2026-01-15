from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA
from .types import (
    ContentTypeEnum,
    MessageCategoryEnum,
    MessageTypeEnum,
    PriorityLevelEnum,
)


class MessageInboxView(Base):
    """
    ORM mapping for the `_message_inbox` view defined via PGView.
    Exposes a flattened dataset that joins messages and recipients to
    support notification fan-out without additional joins.
    """

    __tablename__ = "_message_inbox"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # Core identifiers
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Sender profile fields
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)

    # Recipient profile fields
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)

    # Message content fields
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
    recipient_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)


class MessageOutboxView(Base):
    """
    ORM mapping for the `_message_outbox` view defined via PGView.
    Exposes a flattened dataset that joins messages and recipients to
    support notification fan-out without additional joins.
    """

    __tablename__ = "_message_outbox"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    recipient_id: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)
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
    recipient_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_count: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return (
            f"<MessageOutboxView(message_id={self.message_id}, "
            f"sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
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
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    recipient_id: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)
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
    recipient_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)
    target_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    box_type: Mapped[str] = mapped_column(String)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_count: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return (
            f"<MessageBoxView(message_id={self.message_id}, "
            f"sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
        )


class MessageThreadView(Base):
    """
    ORM mapping for the `_message_thread` view defined via PGView.
    Exposes a flattened dataset that joins messages and recipients to
    support notification fan-out without additional joins.
    """

    __tablename__ = "_message_thread"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)
    recipient_id: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_profile: Mapped[Optional[dict]] = mapped_column(JSON)
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
    recipient_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_count: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return (
            f"<MessageOutboxView(message_id={self.message_id}, "
            f"sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
        )
