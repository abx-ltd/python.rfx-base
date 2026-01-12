"""
Message Service ORM Mapping (Schema Layer)
==========================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``src/rfx_message/model.py``. These models are used for Alembic autogenerate
and lightweight metadata introspection without importing the full message
service stack.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    ActionTypeEnum,
    BoxTypeEnum,
    ContentTypeEnum,
    DeliveryStatusEnum,
    HTTPMethodEnum,
    HTTPTargetEnum,
    MessageTypeEnum,
    PriorityLevelEnum,
    RenderStatusEnum,
    RenderStrategyEnum,
    TagGroupEnum,
    MessageCategoryEnum,
)


class Message(TableBase):
    """Core message entity stored in ``rfx_message.message``."""

    __tablename__ = "message"

    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    subject: Mapped[Optional[str]] = mapped_column(String(1024))
    content: Mapped[Optional[str]] = mapped_column(Text)
    rendered_content: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(
            ContentTypeEnum,
            name="contenttypeenum",
            schema=SCHEMA,
            native_enum=True,
            values_callable=lambda enum: [e.value for e in enum],
        )
    )
    archived: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    is_important: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    expirable: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    request_read_receipt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    priority: Mapped[PriorityLevelEnum] = mapped_column(
        SQLEnum(PriorityLevelEnum, name="prioritylevelenum", schema=SCHEMA),
        default=PriorityLevelEnum.MEDIUM,
        nullable=False,
    )
    message_type: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )
    category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
        SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    )
    delivery_status: Mapped[DeliveryStatusEnum] = mapped_column(
        SQLEnum(DeliveryStatusEnum, name="deliverystatusenum", schema=SCHEMA),
        default=DeliveryStatusEnum.PENDING,
        nullable=False,
    )

    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)

    template_key: Mapped[Optional[str]] = mapped_column(String(255))
    template_version: Mapped[Optional[int]]
    template_locale: Mapped[Optional[str]] = mapped_column(String(10))
    template_engine: Mapped[Optional[str]] = mapped_column(String(32))
    template_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    render_strategy: Mapped[Optional[RenderStrategyEnum]] = mapped_column(
        SQLEnum(RenderStrategyEnum, name="renderstrategyenum", schema=SCHEMA)
    )
    render_status: Mapped[Optional[RenderStatusEnum]] = mapped_column(
        SQLEnum(RenderStatusEnum, name="renderstatusenum", schema=SCHEMA)
    )
    rendered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    render_error: Mapped[Optional[str]] = mapped_column(Text)

    actions: Mapped[List["MessageAction"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient",
        back_populates="message",
        cascade="all, delete-orphan",
        foreign_keys="MessageRecipient.message_id",
    )
    attachments: Mapped[List["MessageAttachment"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    embeds: Mapped[List["MessageEmbedded"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    references: Mapped[List["MessageReference"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class MessageAction(TableBase):
    """Interactive actions rendered with a message."""

    __tablename__ = "message_action"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    type: Mapped[Optional[ActionTypeEnum]] = mapped_column(
        SQLEnum(ActionTypeEnum, schema=SCHEMA)
    )
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(String(1024))

    authentication: Mapped[dict] = mapped_column(JSONB, default=dict)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    host: Mapped[Optional[str]] = mapped_column(String(1024))
    endpoint: Mapped[Optional[str]] = mapped_column(String(1024))
    method: Mapped[Optional[HTTPMethodEnum]] = mapped_column(
        SQLEnum(HTTPMethodEnum, name="httpmethodenum", schema=SCHEMA)
    )
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mobile_endpoint: Mapped[Optional[str]] = mapped_column(String(1024))
    destination: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    target: Mapped[Optional[HTTPTargetEnum]] = mapped_column(
        SQLEnum(HTTPTargetEnum, name="httptargetenum", schema=SCHEMA)
    )

    message: Mapped["Message"] = relationship(back_populates="actions")
    recipient_actions: Mapped[List["MessageRecipientAction"]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
    executed_by: Mapped[List["MessageRecipient"]] = relationship(
        back_populates="executed_action",
        foreign_keys="MessageRecipient.executed_action_id",
    )


class MessageBox(TableBase):
    """Message folders (inbox, sent, custom)."""

    __tablename__ = "message_box"

    _txt: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    email_alias: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[BoxTypeEnum]] = mapped_column(
        SQLEnum(BoxTypeEnum, name="boxtypeenum", schema=SCHEMA)
    )

    users: Mapped[List["MessageBoxUser"]] = relationship(
        back_populates="box", cascade="all, delete-orphan"
    )
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        back_populates="box", cascade="all"
    )


class MessageBoxUser(TableBase):
    """User membership for message boxes."""

    __tablename__ = "message_box_user"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    box_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_box._id"), nullable=False
    )

    box: Mapped["MessageBox"] = relationship(back_populates="users")


class MessageRecipient(TableBase):
    """Recipient-level metadata for a message."""

    __tablename__ = "message_recipient"

    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )
    executed_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_action._id")
    )
    last_reply_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id")
    )
    box_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_box._id")
    )

    read: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mark_as_read: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    archived: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_ignored: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    label: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list
    )
    direction: Mapped[Optional[MessageTypeEnum]] = mapped_column(
        SQLEnum(MessageTypeEnum, name="messagetypeenum", schema=SCHEMA)
    )

    message: Mapped["Message"] = relationship(
        back_populates="recipients", foreign_keys=[message_id]
    )
    executed_action: Mapped[Optional["MessageAction"]] = relationship(
        back_populates="executed_by", foreign_keys=[executed_action_id]
    )
    last_reply: Mapped[Optional["Message"]] = relationship(foreign_keys=[last_reply_id])
    box: Mapped[Optional["MessageBox"]] = relationship(back_populates="recipients")
    actions: Mapped[List["MessageRecipientAction"]] = relationship(
        back_populates="message_recipient", cascade="all, delete-orphan"
    )


class MessageRecipientAction(TableBase):
    """Records execution of actions by recipients."""

    __tablename__ = "message_recipient_action"

    message_recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message_recipient._id"),
        nullable=False,
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_action._id"), nullable=False
    )
    response: Mapped[dict] = mapped_column(JSONB, default=dict)

    message_recipient: Mapped["MessageRecipient"] = relationship(
        back_populates="actions"
    )
    action: Mapped["MessageAction"] = relationship(
        back_populates="recipient_actions", foreign_keys=[action_id]
    )


class MessageAttachment(TableBase):
    """Files linked to a message."""

    __tablename__ = "message_attachment"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), primary_key=True
    )
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    message: Mapped["Message"] = relationship(back_populates="attachments")


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


class Tag(TableBase):
    """Global tags for message classification."""

    __tablename__ = "tag"
    __table_args__ = {"schema": SCHEMA}

    name: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7))
    font_color: Mapped[Optional[str]] = mapped_column(String(7))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    group: Mapped[Optional[TagGroupEnum]] = mapped_column(
        SQLEnum(TagGroupEnum, name="taggroupenum", schema=SCHEMA)
    )


class Label(TableBase):
    """User-defined labels for personal inbox organization."""

    __tablename__ = "label"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7))
    font_color: Mapped[Optional[str]] = mapped_column(String(7))


class TagPreference(TableBase):
    """User preferences for how tags behave or render."""

    __tablename__ = "tag_preference"

    option: Mapped[dict] = mapped_column(JSONB, default=dict)


class RefRole(TableBase):
    """Reference role catalog used by the messaging service."""

    __tablename__ = "ref__role"

    key: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
