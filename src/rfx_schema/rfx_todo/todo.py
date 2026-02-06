"""
RFX Discuss Comment Models
===========================
Core comment and discussion tables.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from . import TableBase, SCHEMA
from .types import TodoStatusEnum


class Todo(TableBase):
    __tablename__ = "todo"
    __table_args__ = {"schema": SCHEMA}

    resource: Mapped[Optional[str]] = mapped_column(String(24))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TodoStatusEnum] = mapped_column(
        SQLEnum(TodoStatusEnum, name="todostatusenum", schema=SCHEMA),
        default=TodoStatusEnum.NEW,
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    data_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
