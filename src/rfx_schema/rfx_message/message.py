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
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    ContentTypeEnum,
    DeliveryStatusEnum,
    MessageTypeEnum,
    PriorityLevelEnum,
    RenderStatusEnum,
    RenderStrategyEnum,
)

if TYPE_CHECKING:
    from .message_action import MessageAction
    from .message_attachment import MessageAttachment
    from .message_embedded import MessageEmbedded
    from .message_recipient import MessageRecipient
    from .message_reference import MessageReference
    from .message_sender import MessageSender


class Message(TableBase):
    """Core message entity stored in ``rfx_message.message``."""

    __tablename__ = "message"

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
    senders: Mapped[List["MessageSender"]] = relationship(
        "MessageSender",
        back_populates="message",
        cascade="all, delete-orphan",
        foreign_keys="MessageSender.message_id",
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