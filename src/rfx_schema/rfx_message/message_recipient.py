from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    DirectionTypeEnum,
)

if TYPE_CHECKING:
    from .message_box import MessageBox
    from .message import Message, MessageAction


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
    is_ignored: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    label: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list
    )
    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA)
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
