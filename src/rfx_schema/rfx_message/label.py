from . import TableBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
import uuid


class Label(TableBase):
    """User-defined labels for personal inbox organization."""

    __tablename__ = "label"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7))
    font_color: Mapped[Optional[str]] = mapped_column(String(7))
