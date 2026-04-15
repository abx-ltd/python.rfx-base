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
        Index("idx_category_mailbox_id_key_deleted","mailbox_id", "key", "_deleted", unique=True),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    mailbox_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.mailbox._id"), nullable=False
    )