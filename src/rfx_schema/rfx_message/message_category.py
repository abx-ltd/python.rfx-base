from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


from . import TableBase, SCHEMA
from .types import (
    MessageCategoryEnum,
)
from sqlalchemy import String


class MessageCategory(TableBase):
    """Message category enumeration."""

    __tablename__ = "message_category"
    category: Mapped[Optional[MessageCategoryEnum]] = mapped_column(
        SQLEnum(MessageCategoryEnum, name="messagecategoryenum", schema=SCHEMA)
    )
    resource: Mapped[Optional[str]] = mapped_column(String(255))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
