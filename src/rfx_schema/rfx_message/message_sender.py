from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    DirectionTypeEnum,
)

if TYPE_CHECKING:
    from .message_box import MessageBox
    from .message import Message


class MessageSender(TableBase):
    __tablename__ = "message_sender"

    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    box_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_box._id")
    )
    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA),
        default=DirectionTypeEnum.OUTBOUND,
    )

    message: Mapped["Message"] = relationship(back_populates="senders")
    box: Mapped[Optional["MessageBox"]] = relationship(back_populates="senders")


class MessageSenderAction(TableBase):
    __tablename__ = "message_sender_action"

    message_sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_sender._id"), nullable=False
    )

    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_action._id"), nullable=False
    )

    response: Mapped[dict] = mapped_column(JSON, default=dict)
