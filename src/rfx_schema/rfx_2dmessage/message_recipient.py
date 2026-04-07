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

    # recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.category._id"), nullable=True
    )

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)

    read: Mapped[bool] = mapped_column(Boolean, default=False)
    mark_as_read: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_ignored: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tag: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=lambda: []
    )
    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA),
        default=DirectionTypeEnum.INBOUND,
    )
    status: Mapped[Optional[MailBoxMessageStatusTypeEnum]] = mapped_column(
        SQLEnum(MailBoxMessageStatusTypeEnum, name="mailboxmessagestatustypeenum", schema=SCHEMA),
        nullable=False,
        default=MailBoxMessageStatusTypeEnum.NEW
    )

    mailbox: Mapped["Mailbox"] = relationship(
        "Mailbox",
        back_populates="message_recipients",
        foreign_keys=[mailbox_id],
    )

    message: Mapped["Message"] = relationship(
        back_populates="recipients", foreign_keys=[message_id]
    )

    actions: Mapped[List["MessageRecipientAction"]] = relationship(
        back_populates="message_recipient", cascade="all, delete-orphan"
    )

    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        foreign_keys=[category_id]
    )


class MessageRecipientAction(TableBase):
    """Records execution of actions by recipients."""

    __tablename__ = "message_recipient_action"
    __table_args__ = (
        Index("idx_mr_action_recipient", "message_recipient_id"),
        Index("idx_mr_action_action", "action_id"),
    )

    message_recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.message_recipient._id"),
        nullable=False,
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_action._id"), nullable=False
    )

    # Input from UI
    input_payload: Mapped[dict] = mapped_column(JSONB, default=lambda: {})

    # Raw response (full envelope)
    response_payload: Mapped[Optional[dict|None]] = mapped_column(JSONB, default=lambda: {})

    status: Mapped[ActionExecutionStatus] = mapped_column(
        SQLEnum(ActionExecutionStatus, name="actionexecutionstatus", schema=SCHEMA),
        nullable=False,
        default=ActionExecutionStatus.PENDING
    )  # success | error

    record_id: Mapped[Optional[str | None]] = mapped_column(String(255))
    response_data: Mapped[dict | None] = mapped_column(JSONB)

    error: Mapped[Optional[dict]] = mapped_column(JSONB)

    # EMBED SUPPORT
    session_id: Mapped[str | None] = mapped_column(String(255))
    callback_payload: Mapped[dict | None] = mapped_column(JSONB)

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    message_recipient: Mapped["MessageRecipient"] = relationship(
        back_populates="actions",
        foreign_keys=[message_recipient_id]
    )

    action: Mapped["MessageAction"] = relationship(
        back_populates="recipient_actions",
        foreign_keys=[action_id]
    )
