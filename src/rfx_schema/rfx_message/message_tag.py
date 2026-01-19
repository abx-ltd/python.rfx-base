from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA

if TYPE_CHECKING:
    pass


class MessageTag(TableBase):
    __tablename__ = "message_tag"
    __table_args__ = {"schema": SCHEMA}

    resource: Mapped[str] = mapped_column(String(255))
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    key: Mapped[str] = mapped_column(String(255))
