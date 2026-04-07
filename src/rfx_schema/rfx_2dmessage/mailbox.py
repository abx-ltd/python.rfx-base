from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
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
    # channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
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
    message_recipients = relationship(
        "MessageRecipient",
        back_populates="mailbox"
    )

class MailboxMember(TableBase):
    __tablename__ = "mailbox_member"
    __table_args__ = ({"schema": SCHEMA},)

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
