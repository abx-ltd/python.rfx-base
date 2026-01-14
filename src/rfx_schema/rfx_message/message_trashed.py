from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from . import TableBase
from sqlalchemy import String, Boolean


class MessageTrashed(TableBase):
    """Message trashed enumeration."""

    __tablename__ = "message_trashed"
    trashed: Mapped[Optional[bool]] = mapped_column(Boolean)
    resource: Mapped[Optional[str]] = mapped_column(String(255))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
