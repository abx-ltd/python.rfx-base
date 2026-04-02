from __future__ import annotations
import uuid
from typing import Optional, Any

from sqlalchemy import Integer, String , Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA 
from  .types import EntryTypeEnum , RealmMetaKeyEnum, EntryStatusEnum


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

    realm_meta: Mapped[dict[RealmMetaKeyEnum, str]] = mapped_column(
        JSON, nullable=False, default=dict
    )
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
    Entry view aligned with entry table columns plus tags aggregation.
    """

    __tablename__ = "_entry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[EntryTypeEnum] = mapped_column(
        SQLEnum(EntryTypeEnum, name="entrytypeenum", schema=SCHEMA), nullable=False
    )
    media_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    status: Mapped[EntryStatusEnum] = mapped_column(
        SQLEnum(EntryStatusEnum, name="entrystatusenum", schema=SCHEMA),
        nullable=False,
    )
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)

    tags: Mapped[Any] = mapped_column(JSON, nullable=False)


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

    entries: Mapped[Any] = mapped_column(JSON, nullable=False)
