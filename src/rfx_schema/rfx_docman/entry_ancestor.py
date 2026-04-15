"""Entry ancestor closure table ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Index, PrimaryKeyConstraint, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import CoreTableBase, SCHEMA


class EntryAncestor(CoreTableBase):
    """
    Closure table for entry hierarchy.

    Every ancestor-descendant pair is stored explicitly,
    including self-links where depth = 0.
    """

    __tablename__ = "entry_ancestor"
    __table_args__ = (
        PrimaryKeyConstraint(
            "ancestor_id",
            "descendant_id",
            name="pkey_entry_ancestor",
        ),
        Index(
            "ix_ea_ancestor_depth",
            "ancestor_id",
            "depth",
        ),
        Index(
            "ix_ea_descendant_depth",
            "descendant_id",
            "depth",
        ),
        CheckConstraint(
            "depth >= 0",
            name="ck_ea_depth_non_negative",
        ),
        CheckConstraint(
            "(depth = 0 AND ancestor_id = descendant_id) OR "
            "(depth > 0 AND ancestor_id != descendant_id)",
            name="ck_ea_self_ref_depth_zero",
        ),
        {"schema": SCHEMA},
    )

    ancestor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.entry._id",
            name="fk_ea_ancestor",
            ondelete="CASCADE",  # hard-delete only (soft-delete does not trigger)
        ),
        nullable=False,
    )
    descendant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.entry._id",
            name="fk_ea_descendant",
            ondelete="CASCADE",  # hard-delete only (soft-delete does not trigger)
        ),
        nullable=False,
    )
    depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
