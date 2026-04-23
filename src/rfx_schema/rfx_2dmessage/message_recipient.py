from __future__ import annotations

from mailbox import Mailbox
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    DirectionTypeEnum,
    MailBoxMessageStatusTypeEnum,
    ActionExecutionStatus
)

if TYPE_CHECKING:
    from .message import Message, MessageAction
    from .message_category import Category


class MessageRecipient(TableBase):
    """Recipient-level metadata for a message."""

    __tablename__ = "message_recipient"

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"),
        primary_key=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"),
        primary_key=True
    )
    # category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    #     UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.category._id"), nullable=True
    # )

    mailbox: Mapped["Mailbox"] = relationship(
        "Mailbox",
        back_populates="message_recipients",
        foreign_keys=[mailbox_id],
    )

    message: Mapped["Message"] = relationship(
        "Message",
        back_populates="recipients", 
        foreign_keys=[message_id]
    )

    # category: Mapped[Optional["Category"]] = relationship(
    #     "Category",
    #     foreign_keys=[category_id]
    # )