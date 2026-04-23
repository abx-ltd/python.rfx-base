from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    JSON,
    Boolean,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    DirectionTypeEnum,
)

if TYPE_CHECKING:
    from .message import Message


class MessageSender(TableBase):
    __tablename__ = "message_sender"

    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # external sender info for cases where sender is outside of system (e.g. email from external)
    external_sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_sender_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message._id", ondelete="CASCADE"),
        nullable=False
    )

    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA),
        default=DirectionTypeEnum.OUTBOUND,
    )

    message: Mapped["Message"] = relationship(
        "Message",
        back_populates="senders"
    )
