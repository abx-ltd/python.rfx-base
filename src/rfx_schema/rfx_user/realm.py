from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TableBase, SCHEMA


class Realm(TableBase):
    __tablename__ = "realm"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(String(2048))
    active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
