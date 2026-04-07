from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    String,
    Index,
    UniqueConstraint,
    Text,
    text
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import DirectionTypeEnum

class Category(TableBase):
    __tablename__ = "category"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "key", "_deleted", name="idx_category_profile_id_key_deleted"
        ),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    mailbox_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=True
    )

    messages: Mapped[List["MessageCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class MessageCategory(TableBase):
    __tablename__ = "message_category"
    __table_args__ = (
        Index("idx_message_category_unique","message_id", "category_id", unique=True, postgresql_where=text("_deleted = null"),),
        {"schema": SCHEMA},
        
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    direction: Mapped[Optional[DirectionTypeEnum]] = mapped_column(
        SQLEnum(DirectionTypeEnum, name="directiontypeenum", schema=SCHEMA),
        default=DirectionTypeEnum.INBOUND,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.category._id"),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(
        back_populates="messages"
    )   
