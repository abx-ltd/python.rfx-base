"""
Notification Service ORM Mapping (Schema Layer)
================================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``src/rfx_notify/model.py``. These models are used for Alembic autogenerate
and lightweight metadata introspection without importing the full notification
service stack.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import List, Optional


from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    NotificationChannelEnum,
    NotificationStatusEnum,
    ProviderTypeEnum,
    NotificationPriorityEnum,
    ContentTypeEnum,
)

class Notification(TableBase):
    """Core notification entity for multi-channel delivery tracking."""

    __tablename__ = "notification"

    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    channel: Mapped[NotificationChannelEnum] = mapped_column(
        SQLEnum(NotificationChannelEnum, name="notificationchannelenum", schema=SCHEMA),
        nullable=False
    )
    provider_type: Mapped[Optional[ProviderTypeEnum]] = mapped_column(
        SQLEnum(ProviderTypeEnum, name="providertypeenum", schema=SCHEMA)
    )

    subject: Mapped[Optional[str]] = mapped_column(String(512))
    body: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        SQLEnum(ContentTypeEnum, name="contenttypeenum", schema=SCHEMA)
    )

    recipient_address: Mapped[Optional[str]] = mapped_column(String(512))

    status: Mapped[NotificationStatusEnum] = mapped_column(
        SQLEnum(NotificationStatusEnum, name="notificationstatusenum", schema=SCHEMA),
        nullable=False
    )
    priority: Mapped[Optional[NotificationPriorityEnum]] = mapped_column(
        SQLEnum(NotificationPriorityEnum, name="notificationpriorityenum", schema=SCHEMA)
    )

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    template_key: Mapped[Optional[str]] = mapped_column(String(255))
    template_version: Mapped[Optional[int]] = mapped_column(Integer)
    template_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    provider_message_id: Mapped[Optional[str]] = mapped_column(String(512))
    provider_response: Mapped[dict] = mapped_column(JSONB, default=dict)

    delivery_logs: Mapped[List["NotificationDeliveryLog"]] = relationship(
        back_populates="notification", cascade="all, delete-orphan"
    )


class NotificationDeliveryLog(TableBase):
    """Detailed delivery attempt logs for notifications."""

    __tablename__ = "notification_delivery_log"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.notification._id"), nullable=False
    )
    provider_type: Mapped[Optional[ProviderTypeEnum]] = mapped_column(
        SQLEnum(ProviderTypeEnum, name="providertypeenum", schema=SCHEMA)
    )

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    status: Mapped[NotificationStatusEnum] = mapped_column(
        SQLEnum(NotificationStatusEnum, name="notificationstatusenum", schema=SCHEMA),
        nullable=False
    )
    status_code: Mapped[Optional[str]] = mapped_column(String(64))

    response: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    notification: Mapped["Notification"] = relationship(back_populates="delivery_logs")


class NotificationPreference(TableBase):
    """User preferences for notification channels."""

    __tablename__ = "notification_preference"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", name="uq_user_channel_preference"),
        {"schema": SCHEMA}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    channel: Mapped[NotificationChannelEnum] = mapped_column(
        SQLEnum(NotificationChannelEnum, name="notificationchannelenum", schema=SCHEMA),
        nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    email_address: Mapped[Optional[str]] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    device_token: Mapped[Optional[str]] = mapped_column(String(512))

    opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency_limit: Mapped[dict] = mapped_column(JSONB, default=dict)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)

    quiet_hours_start: Mapped[Optional[time]] = mapped_column(Time)
    quiet_hours_end: Mapped[Optional[time]] = mapped_column(Time)
    quiet_hours_timezone: Mapped[Optional[str]] = mapped_column(String(64))
