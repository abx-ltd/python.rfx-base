from __future__ import annotations

from datetime import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
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
from .types import MailBoxTypeEnum, MailBoxMemberRoleEnum, MailBoxMessageStatusTypeEnum

if TYPE_CHECKING:
    from .message import Message

class Mailbox(TableBase):
    __tablename__ = "mailbox"
    __table_args__ = ({"schema": SCHEMA},)

    name: Mapped[str] = mapped_column(String(255), nullable=False) # this is channel name by user created
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    telecom_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telecom_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    mailbox_type: Mapped[MailBoxTypeEnum] = mapped_column(
        SQLEnum(MailBoxTypeEnum, name="mailboxtypeenum", schema=SCHEMA),
        default=MailBoxTypeEnum.EMAIL,
    )
    message_recipients = relationship(
        "MessageRecipient",
        back_populates="mailbox"
    )

    messages = relationship(
        "Message",
        back_populates="mailbox",
        cascade="all, delete-orphan"
    )

class MailboxMember(TableBase):
    __tablename__ = "mailbox_member"
    __table_args__ = ({"schema": SCHEMA},
                      Index("ix_mailbox_member", "mailbox_id", "member_id", unique=True),
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[MailBoxMemberRoleEnum] = mapped_column(
        SQLEnum(MailBoxMemberRoleEnum, name="mailboxmemberroleenum", schema=SCHEMA),
        default=MailBoxMemberRoleEnum.VIEWER,
    )

class MessageMailboxState(TableBase):
    __tablename__ = "message_mailbox_state"
    __table_args__ = ({"schema": SCHEMA},
                      Index("ix_message_mailbox_state", "mailbox_id", "message_id", "assigned_to_profile_id", unique=True),
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )
    
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    assigned_to_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    folder: Mapped[str] = mapped_column(String(255), default="inbox")

    read: Mapped[bool] = mapped_column(Boolean, default=False)
    mark_as_read: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_ignored: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # tags: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
    #     ARRAY(UUID(as_uuid=True)), default=lambda: []
    # )

    status: Mapped[Optional[MailBoxMessageStatusTypeEnum]] = mapped_column(
        SQLEnum(MailBoxMessageStatusTypeEnum, name="mailboxmessagestatustypeenum", schema=SCHEMA),
        nullable=False,
        default=MailBoxMessageStatusTypeEnum.NEW
    )

    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)