from __future__ import annotations

from datetime import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    Index,
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TableBase, SCHEMA
from .types import (
    ActionExecutionStatus,
    ActionTypeEnum,
    ExecutionModeEnum,
    HTTPMethodEnum,
    HTTPTargetEnum,
)

if TYPE_CHECKING:
    from .message import Message
    from .message_recipient import MessageRecipient, MessageRecipientAction


class MessageActionExecute(TableBase):
    __tablename__ = "message_action_execute"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id", ondelete="CASCADE"), nullable=False
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_action._id", ondelete="CASCADE"), nullable=False
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # profile who executed the action

    context_mailbox_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )

    execution_mode: Mapped[ExecutionModeEnum] = mapped_column(
        SQLEnum(ExecutionModeEnum, name="executionmodeenum", schema=SCHEMA),
        nullable=False,
        default=ExecutionModeEnum.API
    ) # api | embed

    status: Mapped[ActionExecutionStatus] = mapped_column(
        SQLEnum(ActionExecutionStatus, name="actionexecutionstatus", schema=SCHEMA),
        nullable=False,
        default=ActionExecutionStatus.PENDING
    )

    record_id: Mapped[Optional[str | None]] = mapped_column(String(255), nullable=True)

    # Input from UI
    input_payload_json: Mapped[dict] = mapped_column(JSONB, default=lambda: {}, nullable=True)

    # Raw response (full envelope)
    response_payload_json: Mapped[Optional[dict|None]] = mapped_column(JSONB, default=lambda: {})

    error_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    external_session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    action: Mapped["MessageAction"] = relationship(
        back_populates="recipient_actions",
        foreign_keys=[action_id]
    )

class MessageAction(TableBase):
    """Interactive actions rendered with a message."""

    __tablename__ = "message_action"
    __table_args__ = (
        Index("uq_action_per_mailbox", "mailbox_id", "action_key", unique=True, postgresql_where=text("_deleted IS NULL")),
        CheckConstraint(
            "(action_type IN ('atomic','form') AND execution_mode = 'api') OR "
            "(action_type = 'embedded' AND execution_mode = 'embed')",
            name="chk_type_execution",
        ),

        CheckConstraint(
            "(execution_mode = 'api' AND endpoint_json IS NOT NULL AND embedded_json IS NULL) OR "
            "(execution_mode = 'embed' AND embedded_json IS NOT NULL AND endpoint_json IS NULL)",
            name="chk_execution_payload",
        ),

        CheckConstraint(
            "(action_type = 'form' AND schema_json IS NOT NULL) OR "
            "(action_type <> 'form' AND schema_json IS NULL)",
            name="chk_schema_usage",
        ),
    )

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    mailbox_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id", ondelete="CASCADE"), nullable=True
    )
    action_key: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    action_type: Mapped[ActionTypeEnum] = mapped_column(
        SQLEnum(ActionTypeEnum, name="actiontypeenum", schema=SCHEMA),
        nullable=False
    ) # atomic | form | embedded

    description: Mapped[Optional[str]] = mapped_column(String(1024))

    execution_mode: Mapped[ExecutionModeEnum] = mapped_column(
        SQLEnum(ExecutionModeEnum, name="executionmodeenum", schema=SCHEMA),
        nullable=False
    ) # api | embed

    authorization_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authorization: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # endpoint json
    endpoint_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    embedded_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    schema_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)

    recipient_actions: Mapped[List["MessageActionExecute"]] = relationship(
        "MessageActionExecute",
        back_populates="action", cascade="all, delete-orphan"
    )
