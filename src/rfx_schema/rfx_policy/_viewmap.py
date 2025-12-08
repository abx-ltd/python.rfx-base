from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA


class PolicyUserProfileView(Base):
    """
    ORM mapping for the `_policy__user_profile` view used to materialize Casbin
    policy tuples for user/profile access checks.
    """

    __tablename__ = "_policy__user_profile"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    _id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ptype: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(255))
    sub: Mapped[Optional[str]] = mapped_column(String(255))
    org: Mapped[Optional[str]] = mapped_column(String(255))
    dom: Mapped[Optional[str]] = mapped_column(String(255))
    res: Mapped[Optional[str]] = mapped_column(String(255))
    rid: Mapped[Optional[str]] = mapped_column(String(255))
    act: Mapped[Optional[str]] = mapped_column(String(255))
    cqrs: Mapped[Optional[str]] = mapped_column(String(255))
    meta: Mapped[Optional[str]] = mapped_column(String(255))
    _deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"<PolicyUserProfileView(ptype={self.ptype}, role={self.role}, "
            f"dom={self.dom}, res={self.res})>"
        )


class PolicyIDMProfileView(Base):
    """
    ORM mapping for the `_policy__idm_profile` view used to materialize Casbin
    policy tuples for user/profile access checks.
    """

    __tablename__ = "_policy__idm_profile"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    _id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ptype: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(255))
    sub: Mapped[Optional[str]] = mapped_column(String(255))
    org: Mapped[Optional[str]] = mapped_column(String(255))
    dom: Mapped[Optional[str]] = mapped_column(String(255))
    res: Mapped[Optional[str]] = mapped_column(String(255))
    rid: Mapped[Optional[str]] = mapped_column(String(255))
    act: Mapped[Optional[str]] = mapped_column(String(255))
    cqrs: Mapped[Optional[str]] = mapped_column(String(255))
    meta: Mapped[Optional[str]] = mapped_column(String(255))
    _deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"<PolicyUserProfileView(ptype={self.ptype}, role={self.role}, "
            f"dom={self.dom}, res={self.res})>"
        )
