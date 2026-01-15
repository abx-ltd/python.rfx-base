from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    BoxTypeEnum,
)

if TYPE_CHECKING:
    from .message_recipient import MessageRecipient


class MessageBox(TableBase):
    """Message folders (inbox, sent, custom)."""

    __tablename__ = "message_box"

    _txt: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    key: Mapped[Optional[str]] = mapped_column(String(1024))
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    type: Mapped[Optional[BoxTypeEnum]] = mapped_column(
        SQLEnum(BoxTypeEnum, name="boxtypeenum", schema=SCHEMA)
    )

    users: Mapped[List["MessageBoxUser"]] = relationship(
        back_populates="box", cascade="all, delete-orphan"
    )
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        back_populates="box", cascade="all"
    )


class MessageBoxUser(TableBase):
    """User membership for message boxes."""

    __tablename__ = "message_box_user"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    box_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message_box._id"), nullable=False
    )

    box: Mapped["MessageBox"] = relationship(back_populates="users")
