"""
Realm ORM Model
===============

Top-level organisational boundary for the document management system.

| Table      | Purpose                                | Key Relationships                        |
| ---------- | -------------------------------------- | ---------------------------------------- |
| realm      | Root namespace; groups shelves+cabinets| 1 → N shelves, categories, cabinets      |
| realm_meta | Key-value metadata per realm           | FK → realm                               |
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase


class Realm(TableBase):
    """Root namespace for a document repository."""

    __tablename__ = "realm"

    name:        Mapped[str]         = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    icon:        Mapped[Optional[str]] = mapped_column(String(255),  nullable=True)
    color:       Mapped[Optional[str]] = mapped_column(String(64),   nullable=True)