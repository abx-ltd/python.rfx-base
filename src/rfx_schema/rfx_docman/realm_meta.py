"""
RealmMeta ORM Model
===================

Key-value metadata scoped to a realm. Used for custom structural level labels
(e.g. renaming "Shelf" → "Function") and arbitrary realm-level configuration.

Unique constraint: (realm_id, key) — each key appears at most once per realm.
"""

from __future__ import annotations

import uuid
from sqlalchemy import String, Enum as SQLEnum, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import RealmMetaKeyEnum


class RealmMeta(TableBase):
    """Per-realm key/value configuration store."""

    __tablename__ = "realm_meta"
    __table_args__ = (
        Index(
            "uq_realm_meta_realm_id_key_active",
            "realm_id",
            "key",
            unique=True,
            postgresql_include=["value"],  
            postgresql_where=text("_deleted IS NULL"),
        ),
        {"schema": SCHEMA},
    )
    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    key: Mapped[RealmMetaKeyEnum] = mapped_column(
        SQLEnum(RealmMetaKeyEnum, name="realmmetakeyenum", schema=SCHEMA),
        nullable=False,
    )
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
