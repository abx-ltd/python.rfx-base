from __future__ import annotations
import uuid
from typing import Optional, Any

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class RealmView(TableBase):
    """
    Realm view with shelf list.
    """

    __tablename__ = "_realm"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    realm_meta: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    # Aggregated shelves with counts
    shelves: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)


class ShelfView(TableBase):
    """
    Shelf view with category count.
    """

    __tablename__ = "_shelf"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    category_count: Mapped[int] = mapped_column(Integer, default=0)
    cabinet_count: Mapped[int] = mapped_column(Integer, default=0)
    entry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Aggregated child categories
    categories: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)


class CategoryView(TableBase):
    """
    Category view with cabinet and entry count.
    """

    __tablename__ = "_category"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    shelf_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    cabinet_count: Mapped[int] = mapped_column(Integer, default=0)
    entry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Aggregated child cabinets
    cabinets: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)


class CabinetView(TableBase):
    """
    Cabinet view with entry count.
    """

    __tablename__ = "_cabinet"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    entry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Aggregated child entries
    entries: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)


class EntryView(TableBase):
    """
    Entry view with parent_path calculation.
    """

    __tablename__ = "_entry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Calculated field from PGView
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Aggregated tags (JSON array from entry_tag JOIN tag)
    tags: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)


class TagView(TableBase):
    """
    Tag view — globally shared tags with aggregated entry list.
    """

    __tablename__ = "_tag"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Aggregated entries (JSON array from entry_tag JOIN entry)
    entries: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
