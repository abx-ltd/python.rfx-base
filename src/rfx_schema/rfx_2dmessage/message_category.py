from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    String,
    Index
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import DirectionTypeEnum

class Category(TableBase):

    __table_name__ = "category"

    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    messages: Mapped[List["MessageCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class MessageCategory(TableBase):
    __table_name__ = "message_category"
    __table_args__ = (
        Index("message_id", "category_id", unique=True),
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
