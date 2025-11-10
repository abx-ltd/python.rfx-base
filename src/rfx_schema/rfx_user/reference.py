"""
Reference Tables Mapping
========================

Static lookup tables that support the user domain. These models simply expose
lookup data (actions, realms, organization types, etc.) and are referenced by
other aggregates via foreign keys.

| Table                  | Purpose                                      |
| ---------------------- | -------------------------------------------- |
| ref__action            | Valid user actions (used by user_action)     |
| ref__organization_type | Organization classification lookup           |
| ref__realm             | Authentication realm names                   |
| ref__role_type         | Role type categories                         |
| ref__system_role       | System-wide roles available to assignments   |
| ref__provider          | OAuth / IdP provider catalog                 |
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class RefAction(TableBase):
    __tablename__ = "ref__action"

    key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))


class RefOrganizationType(TableBase):
    __tablename__ = "ref__organization_type"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))


class RefRealm(TableBase):
    __tablename__ = "ref__realm"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))


class RefRoleType(TableBase):
    __tablename__ = "ref__role_type"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))


class RefSystemRole(TableBase):
    __tablename__ = "ref__system_role"

    description: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    key: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_owner: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_default_signer: Mapped[Optional[bool]] = mapped_column(Boolean)
    default_role: Mapped[Optional[bool]] = mapped_column(Boolean)
    official_role: Mapped[Optional[bool]] = mapped_column(Boolean)
    priority: Mapped[Optional[int]] = mapped_column(Integer)
    role_type: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(f"{SCHEMA}.ref__role_type.key")
    )


class RefProvider(TableBase):
    __tablename__ = "ref__provider"

    _iid: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(Text)
