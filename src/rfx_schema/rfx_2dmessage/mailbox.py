from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import MailBoxTypeEnum, MailBoxMessageStatusTypeEnum

if TYPE_CHECKING:
    from .message import Message

class Mailbox(TableBase):
    __tablename__ = "mailbox"
    __table_args__ = ({"schema": SCHEMA},)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    telecom_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telecom_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    mailbox_type: Mapped[MailBoxTypeEnum] = mapped_column(
        SQLEnum(MailBoxTypeEnum, name="mailboxtypeenum", schema=SCHEMA),
        default=MailBoxTypeEnum.EMAIL,
    )


class MailboxMessage(TableBase):
    __tablename__ = "mailbox_message"
    __table_args__ = (
        Index("idx_mailbox_message_unique", "mailbox_id", "source", "source_id", unique=True),
        Index("idx_mailbox_message_id_unique", "message_id", unique=True, postgresql_where="message_id IS NOT NULL"),
        {"schema": SCHEMA},
    )

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.category._id"), nullable=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    direction: Mapped[Optional[str]] = mapped_column(String(64), nullable=False, default="INBOUND")
    status: Mapped[Optional[MailBoxMessageStatusTypeEnum]] = mapped_column(
        SQLEnum(MailBoxMessageStatusTypeEnum, name="mailboxmessagestatustypeenum", schema=SCHEMA),
        nullable=False,
        default=MailBoxMessageStatusTypeEnum.NEW
    )

    mailbox: Mapped["Mailbox"] = relationship("Mailbox", back_populates="messages")
    message: Mapped[Optional["Message"]] = relationship(
        "Message",
        back_populates="mailbox_messages",
        cascade="all, delete"
    )


Mailbox.messages = relationship(
    "MailboxMessage",
    back_populates="mailbox",
    cascade="all, delete-orphan",
)
