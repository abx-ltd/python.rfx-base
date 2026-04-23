from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    Index,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import MessageLinkTypeEnum

class MessageLink(TableBase):
    __tablename__ = "message_link"
    __table_args__ = (
        UniqueConstraint(
            "left_message_id",
            "right_message_id",
            "link_type",
            name="uq_message_link_left_right_type",
        ),
        Index("ix_message_link_left",  "left_message_id"),
        Index("ix_message_link_right", "right_message_id"),
        Index("ix_message_link_type",  "link_type"),
    )

    left_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message._id"),
        nullable=False,
    )

    right_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message._id"),
        nullable=False,
    )

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.mailbox._id"),
        nullable=False,
    )

    link_type: Mapped[MessageLinkTypeEnum] = mapped_column(
        SQLEnum(
            MessageLinkTypeEnum,
            name="messagelinktypeenum",
            schema=SCHEMA,
        ),
        nullable=False,
        default=MessageLinkTypeEnum.RELATED,
        server_default=MessageLinkTypeEnum.RELATED.value,
    )