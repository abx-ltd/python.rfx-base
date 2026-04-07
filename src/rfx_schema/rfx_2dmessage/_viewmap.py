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
    MailBoxTypeEnum,
    MailBoxMessageStatusTypeEnum,
)

class MessageSenderDetailView(Base):
    __table_name__ = "_message_sender_detail"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}
    
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    # Message information
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    subject: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )
    priority: Mapped[Optional[PriorityLevelEnum]] = mapped_column(
        SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA)
    )
    message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )
    category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
        SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    )
    message_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    message_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # box_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    box_key: Mapped[Optional[str]] = mapped_column(String)
    box_name: Mapped[Optional[str]] = mapped_column(String)
    box_type_enum: Mapped[Optional[BoxTypeEnum]] = mapped_column(
        SQLEnum(BoxTypeEnum, name="boxtypeenum", schema=SCHEMA)
    )
    
    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA)
    )
    
    sender_profile: Mapped[Optional[dict]] = mapped_column(JSON)    

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
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

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


class MessageView(Base):
    """
    ORM mapping for the `_message` view defined via PGView.
    Provides a flattened view of all messages with aggregated counts
    and key message attributes.
    """

    __tablename__ = "_message"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    subject: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(String)
    rendered_content: Mapped[Optional[str]] = mapped_column(String)
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )
    is_important: Mapped[Optional[bool]] = mapped_column(Boolean)
    expirable: Mapped[Optional[bool]] = mapped_column(Boolean)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    request_read_receipt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    priority: Mapped[Optional[PriorityLevelEnum]] = mapped_column(
        SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA)
    )
    message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )
    delivery_status: Mapped[Optional[str]] = mapped_column(String)
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    context: Mapped[Optional[dict]] = mapped_column(JSON)
    category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
        SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    )
    template_key: Mapped[Optional[str]] = mapped_column(String)
    template_version: Mapped[Optional[int]] = mapped_column(Integer)
    template_locale: Mapped[Optional[str]] = mapped_column(String)
    template_engine: Mapped[Optional[str]] = mapped_column(String)
    template_data: Mapped[Optional[dict]] = mapped_column(JSON)
    render_strategy: Mapped[Optional[str]] = mapped_column(String)
    render_status: Mapped[Optional[str]] = mapped_column(String)
    rendered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    render_error: Mapped[Optional[str]] = mapped_column(String)
    is_archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_starred: Mapped[Optional[bool]] = mapped_column(Boolean)
    sender_count: Mapped[Optional[int]] = mapped_column(Integer)
    recipient_count: Mapped[Optional[int]] = mapped_column(Integer)
    attachment_count: Mapped[Optional[int]] = mapped_column(Integer)
    mailbox_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<MessageView(message_id={self.message_id}, "
            f"subject={self.subject})>"
        )


class MailboxView(Base):
    """
    ORM mapping for the `_mailbox` view defined via PGView.
    Provides a flattened view of mailbox and all messages within it,
    including complete message attributes, senders, and recipients.
    """

    __tablename__ = "_mailbox"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # Mailbox Information
    _id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    mailbox_name: Mapped[Optional[str]] = mapped_column(String)
    mailbox_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    telecom_phone: Mapped[Optional[str]] = mapped_column(String)
    telecom_email: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    resource: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String)
    mailbox_type: Mapped[Optional[MailBoxTypeEnum]] = mapped_column(
        SQLEnum(MailBoxTypeEnum, name="mailboxtypeenum", schema=SCHEMA)
    )
    
    # MailboxMessage Information
    message: Mapped[List[dict]] = mapped_column(JSON)
    message_id: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    
    # mailbox_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # source: Mapped[Optional[str]] = mapped_column(String)
    # source_id: Mapped[Optional[str]] = mapped_column(String)
    # category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # message_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
    #     SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA)
    # )
    # status: Mapped[Optional[MailBoxMessageStatusTypeEnum]] = mapped_column(
    #     SQLEnum(MailBoxMessageStatusTypeEnum, name="mailboxmessagestatustypeenum", schema=SCHEMA)
    # )
    # mm_created: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # mm_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # # Message Information
    # message_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # subject: Mapped[Optional[str]] = mapped_column(String)
    # content: Mapped[Optional[str]] = mapped_column(String)
    # rendered_content: Mapped[Optional[str]] = mapped_column(String)
    # content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
    #     SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    # )
    # is_important: Mapped[Optional[bool]] = mapped_column(Boolean)
    # expirable: Mapped[Optional[bool]] = mapped_column(Boolean)
    # expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # request_read_receipt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # priority: Mapped[Optional[PriorityLevelEnum]] = mapped_column(
    #     SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA)
    # )
    # message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
    #     SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    # )
    # delivery_status: Mapped[Optional[str]] = mapped_column(String)
    # data: Mapped[Optional[dict]] = mapped_column(JSON)
    # context: Mapped[Optional[dict]] = mapped_column(JSON)
    # category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
    #     SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    # )
    # template_key: Mapped[Optional[str]] = mapped_column(String)
    # template_version: Mapped[Optional[int]] = mapped_column(Integer)
    # template_locale: Mapped[Optional[str]] = mapped_column(String)
    # template_engine: Mapped[Optional[str]] = mapped_column(String)
    # template_data: Mapped[Optional[dict]] = mapped_column(JSON)
    # render_strategy: Mapped[Optional[str]] = mapped_column(String)
    # render_status: Mapped[Optional[str]] = mapped_column(String)
    # rendered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # render_error: Mapped[Optional[str]] = mapped_column(String)
    # is_archived: Mapped[Optional[bool]] = mapped_column(Boolean)
    # is_starred: Mapped[Optional[bool]] = mapped_column(Boolean)
    # message_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # message_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # creator: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # updater: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # etag: Mapped[Optional[int]] = mapped_column(Integer)

    # # Senders and Recipients
    # senders: Mapped[Optional[dict]] = mapped_column(JSON)
    # recipients: Mapped[Optional[dict]] = mapped_column(JSON)
    # attachment_count: Mapped[Optional[int]] = mapped_column(Integer)
    # action_count: Mapped[Optional[int]] = mapped_column(Integer)

    # def __repr__(self) -> str:
    #     return (
    #         f"<MailboxView(mailbox_id={self.mailbox_id}, "
    #         f"message_id={self.message_id})>"
    #     )
