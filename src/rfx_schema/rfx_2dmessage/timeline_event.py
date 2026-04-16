from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Index,
    DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from . import TableBase, SCHEMA
from fluvius.data import UUID_TYPE
from sqlalchemy.dialects.postgresql import UUID


class TimelineEvent(TableBase):
    """Timeline events for tracking actions on a message."""

    __tablename__ = "timeline_event"
    __table_args__ = (
        Index("ix_timeline_event_message_id", "message_id"),
        Index("ix_timeline_event_event_type", "event_type"),
        Index("ix_timeline_event_actor", "actor_profile_id"),
    )

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.mailbox._id"),
        nullable=False,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message._id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String, nullable=False)

    actor_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )