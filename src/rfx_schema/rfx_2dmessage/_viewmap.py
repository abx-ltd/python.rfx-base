from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

class MailboxView(Base):
    """
    ORM mapping for `_mailbox` VIEW.

    This view aggregates:
    - mailbox info
    - member_ids (uuid[])
    - message_id (uuid[])
    - message (jsonb array with full message + state + tags + attachments)
    """

    __tablename__ = "_mailbox"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # =========================
    # BASE
    # =========================
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    mailbox_name: Mapped[str] = mapped_column(String)
    _created: Mapped[Optional[str]] = mapped_column()
    _updated: Mapped[Optional[str]] = mapped_column()
    _deleted: Mapped[Optional[str]] = mapped_column()

    # =========================
    # MAILBOX
    # =========================
    mailbox_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    telecom_phone: Mapped[Optional[str]] = mapped_column(String)
    telecom_email: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String)

    mailbox_type: Mapped[Optional[MailBoxTypeEnum]] = mapped_column(
        SQLEnum(MailBoxTypeEnum, name="mailboxtypeenum", schema=SCHEMA)
    )

    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    members: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)
    # categories: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)
    # tags: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)


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

class MessageMailboxView(Base):
    __tablename__ = "_message_mailbox"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # =========================
    # PRIMARY KEY
    # =========================
    mailbox_message_state_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    # =========================
    # METADATA (pgentity standard)
    # =========================
    _created: Mapped[datetime] = mapped_column()
    _updated: Mapped[Optional[datetime]] = mapped_column()
    _deleted: Mapped[Optional[datetime]] = mapped_column()

    # =========================
    # MAILBOX
    # =========================
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    mailbox_name: Mapped[str] = mapped_column(String)

    # =========================
    # ASSIGNMENT
    # =========================
    assigned_to_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # =========================
    # MESSAGE STATE
    # =========================
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    folder: Mapped[str] = mapped_column(String)
    is_starred: Mapped[bool] = mapped_column()
    read_at: Mapped[Optional[datetime]] = mapped_column()
    status: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # MESSAGE
    # =========================
    subject: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column()
    message_created_at: Mapped[datetime] = mapped_column()

    priority: Mapped[Optional[str]] = mapped_column(String)
    message_type: Mapped[Optional[str]] = mapped_column(String)
    is_important: Mapped[Optional[bool]] = mapped_column()

    # =========================
    # CATEGORY
    # =========================
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    category_name: Mapped[Optional[str]] = mapped_column(String)
    category_key: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # TAGS
    # =========================
    tags: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)

    # =========================
    # ATTACHMENTS
    # =========================
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)


class MessageDetailView(Base):
    """
    ORM mapping for `_message_mailbox_state` VIEW.

    This view aggregates message mailbox state with full message details,
    including sender, recipients, categories, tags, attachments, and actions.
    """

    __tablename__ = "_message_detail"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # Primary key from message_mailbox_state
    mailbox_message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    # Timestamps
    _created: Mapped[Optional[str]] = mapped_column()
    _updated: Mapped[Optional[str]] = mapped_column()
    _deleted: Mapped[Optional[str]] = mapped_column()

    # Mailbox info
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    mailbox_name: Mapped[str] = mapped_column(String)

    # Message info
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    assigned_to_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    folder: Mapped[str] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String)
    is_starred: Mapped[bool] = mapped_column()

    # Sender and recipients
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Message content
    subject: Mapped[str] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column()
    rendered_content: Mapped[Optional[str]] = mapped_column()
    content_type: Mapped[Optional[str]] = mapped_column(String)
    priority: Mapped[Optional[str]] = mapped_column(String)
    message_type: Mapped[Optional[str]] = mapped_column(String)

    # Message metadata
    expirable: Mapped[Optional[bool]] = mapped_column()
    expiration_date: Mapped[Optional[str]] = mapped_column()

    # Category info
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    category_name: Mapped[Optional[str]] = mapped_column(String)
    category_key: Mapped[Optional[str]] = mapped_column(String)

    # Tags
    tags: Mapped[Optional[List[dict]]] = mapped_column(JSONB)

    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSONB)

    # Actions
    actions: Mapped[Optional[List[dict]]] = mapped_column(JSONB)


class MessageTagView(Base):
    __tablename__ = "_message_tag"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # =========================
    # ROW IDENTIFIER
    # =========================
    message_tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    # =========================
    # MESSAGE
    # =========================
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    subject: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column()
    rendered_content: Mapped[Optional[str]] = mapped_column(String)
    content_type: Mapped[Optional[str]] = mapped_column(String)
    is_important: Mapped[Optional[bool]] = mapped_column(Boolean)
    priority: Mapped[Optional[str]] = mapped_column(String)
    message_type: Mapped[Optional[str]] = mapped_column(String)
    message_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # =========================
    # CATEGORY
    # =========================
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    category_name: Mapped[Optional[str]] = mapped_column(String)
    category_key: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # TAG
    # =========================
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    tag_key: Mapped[Optional[str]] = mapped_column(String)
    tag_name: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # MAILBOX
    # =========================
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    mailbox_name: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # ASSIGNMENT
    # =========================
    assigned_to_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # =========================
    # MESSAGE STATE
    # =========================
    mailbox_message_state_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    folder: Mapped[str] = mapped_column(String)
    is_starred: Mapped[bool] = mapped_column()
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[str]] = mapped_column(String)
    is_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # =========================
    # ATTACHMENTS
    # =========================
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)

    # # =========================
    # # METADATA
    # # =========================
    # _created: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _realm: Mapped[Optional[str]] = mapped_column(String)
    # _creator: Mapped[Optional[str]] = mapped_column(String)
    # _updater: Mapped[Optional[str]] = mapped_column(String)
    # _etag: Mapped[Optional[str]] = mapped_column(String)


class MessageCategoryView(Base):
    __tablename__ = "_message_category"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    # =========================
    # UNIQUE MESSAGE ROW
    # =========================
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    # =========================
    # CATEGORY RELATION
    # =========================
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # =========================
    # MAILBOX
    # =========================
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    mailbox_name: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # ASSIGNMENT
    # =========================
    assigned_to_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # =========================
    # MESSAGE STATE
    # =========================
    mailbox_message_state_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    folder: Mapped[str] = mapped_column(String)
    is_starred: Mapped[bool] = mapped_column()
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[str]] = mapped_column(String)
    is_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # =========================
    # MESSAGE
    # =========================
    subject: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column()
    rendered_content: Mapped[Optional[str]] = mapped_column(String)
    content_type: Mapped[Optional[str]] = mapped_column(String)
    is_important: Mapped[Optional[bool]] = mapped_column(Boolean)
    priority: Mapped[Optional[str]] = mapped_column(String)
    message_type: Mapped[Optional[str]] = mapped_column(String)
    message_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # =========================
    # CATEGORY
    # =========================
    category_name: Mapped[Optional[str]] = mapped_column(String)
    category_key: Mapped[Optional[str]] = mapped_column(String)

    # =========================
    # ATTACHMENTS
    # =========================
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB)

    # # =========================
    # # METADATA
    # # =========================
    # _created: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # _realm: Mapped[Optional[str]] = mapped_column(String)
    # _creator: Mapped[Optional[str]] = mapped_column(String)
    # _updater: Mapped[Optional[str]] = mapped_column(String)
    # _etag: Mapped[Optional[str]] = mapped_column(String)
