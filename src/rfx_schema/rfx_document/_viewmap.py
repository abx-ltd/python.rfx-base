
from __future__ import annotations
from typing import Optional

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class ShelfView(TableBase):
    """
    Shelf view with category count.
    """

    __tablename__ = "_shelf"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    category_count: Mapped[int] = mapped_column(Integer, default=0)
    cabinet_count: Mapped[int] = mapped_column(Integer, default=0)
    entry_count: Mapped[int] = mapped_column(Integer, default=0)


class CategoryView(TableBase):
    """
    Category view with cabinet and entry count.
    """

    __tablename__ = "_category"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shelf_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    cabinet_count: Mapped[int] = mapped_column(Integer, default=0)
    entry_count: Mapped[int] = mapped_column(Integer, default=0)


class CabinetView(TableBase):
    """
    Cabinet view with entry count.
    """

    __tablename__ = "_cabinet"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    category_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

class EntryView(TableBase):
    """
    Entry view with parent_path calculation.
    """

    __tablename__ = "_entry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    cabinet_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Calculated field from PGView
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)