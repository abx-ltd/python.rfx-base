from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Enum as SQLEnum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TableBase, SCHEMA
from .types import (
    ActionTypeEnum,
    ExecutionModeEnum,
    HTTPMethodEnum,
    HTTPTargetEnum,
)

if TYPE_CHECKING:
    from .message import Message
    from .message_recipient import MessageRecipient, MessageRecipientAction


class MessageAction(TableBase):
    """Interactive actions rendered with a message."""

    __tablename__ = "message_action"
    __table_args__ = (
        # schema constraint
        CheckConstraint(
            """
            (type = 'form' AND execution_mode = 'api' AND schema IS NOT NULL)
            OR
            (type = 'atomic' AND schema IS NULL)
            OR
            (type = 'embedded' AND execution_mode = 'embed' AND schema IS NULL)
            """,
            name="check_action_type_schema_execution"
        ),
    )

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), nullable=False
    )

    action_type: Mapped[ActionTypeEnum] = mapped_column(
        SQLEnum(ActionTypeEnum, name="action_type", schema=SCHEMA),
        nullable=False
    )

    name: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(String(1024))

    # Execution (NEW SPEC CORE)
    execution_mode: Mapped[ExecutionModeEnum] = mapped_column(
        SQLEnum(ExecutionModeEnum, name="execution_mode", schema=SCHEMA),
        nullable=False
    )

    execution: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    # Schema (form only)
    schema: Mapped[Optional[dict|None]] = mapped_column(JSONB)

    # # Endpoint (normalized)
    # endpoint_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    # method: Mapped[str] = mapped_column(String(10), nullable=False, default="POST")
    # headers: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Response contract
    response: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # authentication: Mapped[dict] = mapped_column(JSONB, default=dict)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    message: Mapped["Message"] = relationship(back_populates="actions")
    recipient_actions: Mapped[List["MessageRecipientAction"]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
