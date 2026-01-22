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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class Todo(TableBase):
    __tablename__ = "todo"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    assignee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
