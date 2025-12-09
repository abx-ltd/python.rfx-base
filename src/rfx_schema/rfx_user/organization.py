"""
Organization Aggregate ORM Mapping
==================================

The organization aggregate stores multi-tenant account data, delegated access,
custom roles, and status history.

| Table                      | Purpose                                 | Key Relationships                       |
| -------------------------- | --------------------------------------- | --------------------------------------- |
| organization               | Tenant root entity                      | 1 → N profiles, roles, invitations      |
| organization_delegated_access | Cross-organization delegation        | FK → organization (owner & delegate)    |
| organization_role          | Custom roles defined per organization   | FK → organization                       |
| organization_status        | Status transition audit trail           | FK → organization                       |
"""

from __future__ import annotations

from datetime import datetime
import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import from local types to avoid rfx_user module initialization
from .types import OrganizationStatusEnum

from . import TableBase, SCHEMA

if TYPE_CHECKING:  # pragma: no cover
    from .profile import Profile
    from .invitation import Invitation


class Organization(TableBase):
    """Tenant record for the `rfx_user.organization` table."""

    __tablename__ = "organization"

    description: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    system_entity: Mapped[Optional[bool]] = mapped_column(Boolean)
    business_name: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    system_tag: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    user_tag: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    organization_code: Mapped[Optional[str]] = mapped_column(String(255))

    status: Mapped[OrganizationStatusEnum] = mapped_column(
        SQLEnum(
            OrganizationStatusEnum,
            name="organizationstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    invitation_code: Mapped[Optional[str]] = mapped_column(String(10))
    type_key: Mapped[Optional[str]] = mapped_column(
        "type", ForeignKey(f"{SCHEMA}.ref__organization_type.key")
    )

    delegated_access: Mapped[List["OrganizationDelegatedAccess"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    delegated_to_us: Mapped[List["OrganizationDelegatedAccess"]] = relationship(
        back_populates="delegated_organization",
        foreign_keys="OrganizationDelegatedAccess.delegated_organization_id",
    )
    roles: Mapped[List["OrganizationRole"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["OrganizationStatus"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        back_populates="organization", cascade="all"
    )


class OrganizationDelegatedAccess(TableBase):
    """Cross organization delegation records."""

    __tablename__ = "organization_delegated_access"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organization._id"), nullable=True
    )
    delegated_organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organization._id"), nullable=True
    )
    access_scope: Mapped[Optional[str]] = mapped_column(String(255))

    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="delegated_access",
        foreign_keys=[organization_id],
    )
    delegated_organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="delegated_to_us",
        foreign_keys=[delegated_organization_id],
    )


class OrganizationRole(TableBase):
    """Custom role definitions created within an organization."""

    __tablename__ = "organization_role"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    _txt: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    key: Mapped[Optional[str]] = mapped_column(String(255))

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organization._id"), nullable=False
    )

    organization: Mapped["Organization"] = relationship(back_populates="roles")


class OrganizationStatus(TableBase):
    """History of organization status transitions."""

    __tablename__ = "organization_status"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organization._id"), nullable=False
    )
    src_state: Mapped[OrganizationStatusEnum] = mapped_column(
        SQLEnum(
            OrganizationStatusEnum,
            name="organizationstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    dst_state: Mapped[OrganizationStatusEnum] = mapped_column(
        SQLEnum(
            OrganizationStatusEnum,
            name="organizationstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(Text)

    organization: Mapped["Organization"] = relationship(back_populates="status_history")
