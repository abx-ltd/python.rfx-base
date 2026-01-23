"""
RFX Discuss Comment Models
===========================
Core comment and discussion tables.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    String,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from . import TableBase, SCHEMA


class Todo(TableBase):
    __tablename__ = "todo"
    __table_args__ = {"schema": SCHEMA}

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    scope_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)


class TodoItem(TableBase):
    __tablename__ = "todo_item"
    __table_args__ = {"schema": SCHEMA}

    todo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
