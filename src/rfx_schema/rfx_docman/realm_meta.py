"""
RealmMeta ORM Model
===================

Key-value metadata scoped to a realm. Used for custom structural level labels
(e.g. renaming "Shelf" → "Function") and arbitrary realm-level configuration.

Unique constraint: (realm_id, key) — each key appears at most once per realm.
"""

from __future__ import annotations

import uuid
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class RealmMeta(TableBase):
    """Per-realm key/value configuration store."""

    __tablename__ = "realm_meta"
    __table_args__ = (
        UniqueConstraint("realm_id", "key", name="uq_realm_meta_realm_id_key"),
        {"schema": SCHEMA},
    )

    realm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
