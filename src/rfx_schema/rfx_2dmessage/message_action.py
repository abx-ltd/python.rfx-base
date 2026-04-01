from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TableBase, SCHEMA
from .types import (
    ActionTypeEnum,
    HTTPMethodEnum,
    HTTPTargetEnum,
)

if TYPE_CHECKING:
    from .message import Message
    from .message_recipient import MessageRecipient, MessageRecipientAction


class MessageAction(TableBase):
    """Interactive actions rendered with a message."""

    __tablename__ = "message_action"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    type: Mapped[Optional[ActionTypeEnum]] = mapped_column(
        SQLEnum(ActionTypeEnum, schema=SCHEMA)
    )
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(String(1024))

    authentication: Mapped[dict] = mapped_column(JSONB, default=dict)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    host: Mapped[Optional[str]] = mapped_column(String(1024))
    endpoint: Mapped[Optional[str]] = mapped_column(String(1024))
    method: Mapped[Optional[HTTPMethodEnum]] = mapped_column(
        SQLEnum(HTTPMethodEnum, name="httpmethodenum", schema=SCHEMA)
    )
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mobile_endpoint: Mapped[Optional[str]] = mapped_column(String(1024))
    destination: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    target: Mapped[Optional[HTTPTargetEnum]] = mapped_column(
        SQLEnum(HTTPTargetEnum, name="httptargetenum", schema=SCHEMA)
    )

    message: Mapped["Message"] = relationship(back_populates="actions")
    recipient_actions: Mapped[List["MessageRecipientAction"]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
    executed_by: Mapped[List["MessageRecipient"]] = relationship(
        back_populates="executed_action",
        foreign_keys="MessageRecipient.executed_action_id",
    )
