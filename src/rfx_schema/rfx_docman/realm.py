"""
Realm ORM Model
===============

Top-level organisational boundary for the document management system.

"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String , Index, text
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase , SCHEMA


class Realm(TableBase):
    """Root namespace for a document repository."""

    __tablename__ = "realm"
    __table_args__ = (
        Index(
            "uq_realm_name_active",
            "name",
            unique=True,
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )

    name:        Mapped[str]         = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    icon:        Mapped[Optional[str]] = mapped_column(String(255),  nullable=True)
    color:       Mapped[Optional[str]] = mapped_column(String(64),   nullable=True)