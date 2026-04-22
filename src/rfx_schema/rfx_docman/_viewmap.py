from __future__ import annotations
from datetime import datetime
import uuid
from typing import Optional

from fluvius.casbin import PolicySchema

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, PolicyBase, SCHEMA, RFX_POLICY_SCHEMA
from .types import RealmMetaKeyEnum


class RealmView(TableBase):
    """Realm view with realm metadata and shelf counts."""

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
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=False
    )


class ShelfView(TableBase):
    """Shelf view with aggregated category counts."""

    __tablename__ = "_shelf"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate fields
    category_count: Mapped[int] = mapped_column(Integer, default=0)


class CategoryView(TableBase):
    """Category view with aggregated cabinet counts."""

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
    """Cabinet view with aggregated entry counts."""

    __tablename__ = "_cabinet"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    entry_count: Mapped[int] = mapped_column(Integer, default=0)


class EntryView(TableBase):
    """Entry view enriched with media metadata and tag payload."""

    __tablename__ = "_entry"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(2561), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_virtual: Mapped[bool] = mapped_column(Boolean, nullable=False)
    media_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    filemime: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    length: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    child_entry_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)


class EntryBinView(TableBase):
    """Entry bin view for soft-deleted entries."""

    __tablename__ = "_entry_bin"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cabinet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parent_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(2561), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_virtual: Mapped[bool] = mapped_column(Boolean, nullable=False)
    media_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    filemime: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    length: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    child_entry_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)


class PolicyDocmanView(PolicyBase, PolicySchema):
    __tablename__ = "_policy__docman_profile"
    __table_args__ = {"schema": RFX_POLICY_SCHEMA, "info": {"is_view": True}}
