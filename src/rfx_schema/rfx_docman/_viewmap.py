from __future__ import annotations
import uuid
from typing import Optional

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA 
from  .types import  RealmMetaKeyEnum


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
    shelf_count: Mapped[int] = mapped_column(Integer, default=0)

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

    entry_count: Mapped[int] = mapped_column(Integer, default=0)

class EntryView(TableBase):
    """
    Entry view.
    """

    __tablename__ = "_entry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(2561), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    media_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    filename: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    filehash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    filemime: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    length: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    resource__id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)


class TagView(TableBase):
    """
    Tag view. Supports optional filtering by cabinet via _tag view rows.
    """

    __tablename__ = "_tag"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cabinet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
