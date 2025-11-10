"""
Profile Aggregate ORM Mapping
=============================

Profiles capture user context inside an organization along with status and role
assignments, device locations, and related audit trails.

| Table            | Purpose                               | Key Relationships                           |
| ---------------- | ------------------------------------- | ------------------------------------------- |
| profile          | User representation within org scope  | FK → user, organization; 1 → N roles/groups |
| profile_status   | Status history for a profile          | FK → profile                                |
| profile_role     | Assigned roles for the profile        | FK → profile                                |
| profile_location | Device/activity tracking              | FK → profile                                |
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import from local types to avoid rfx_user module initialization
from .types import ProfileStatusEnum

from . import TableBase, SCHEMA

if TYPE_CHECKING:  # pragma: no cover
    from .user import User
    from .organization import Organization
    from .invitation import Invitation
    from .group import ProfileGroup


class Profile(TableBase):
    """User profile definition within an organization."""

    __tablename__ = "profile"

    access_tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    active: Mapped[Optional[bool]] = mapped_column(Boolean)

    address__city: Mapped[Optional[str]] = mapped_column(String(1024))
    address__country: Mapped[Optional[str]] = mapped_column(String(1024))
    address__line1: Mapped[Optional[str]] = mapped_column(String(1024))
    address__line2: Mapped[Optional[str]] = mapped_column(String(1024))
    address__postal: Mapped[Optional[str]] = mapped_column(String(1024))
    address__state: Mapped[Optional[str]] = mapped_column(String(1024))

    picture_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    birthdate: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    gender: Mapped[Optional[str]] = mapped_column(String(1024))

    language: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name__family: Mapped[Optional[str]] = mapped_column(String(1024))
    name__given: Mapped[Optional[str]] = mapped_column(String(1024))
    name__middle: Mapped[Optional[str]] = mapped_column(String(1024))
    name__prefix: Mapped[Optional[str]] = mapped_column(String(1024))
    name__suffix: Mapped[Optional[str]] = mapped_column(String(1024))

    realm: Mapped[Optional[str]] = mapped_column(String(1024))
    svc_access: Mapped[Optional[str]] = mapped_column(String(1024))
    svc_secret: Mapped[Optional[str]] = mapped_column(String(1024))
    user_tag: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    telecom__email: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__fax: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(1024))

    tfa_method: Mapped[Optional[str]] = mapped_column(String(1024))
    tfa_token: Mapped[Optional[str]] = mapped_column(String(1024))
    two_factor_authentication: Mapped[Optional[bool]] = mapped_column(Boolean)

    upstream_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    user_type: Mapped[Optional[str]] = mapped_column(String(1024))
    username: Mapped[Optional[str]] = mapped_column(String(1024))

    verified_email: Mapped[Optional[str]] = mapped_column(String(1024))
    verified_phone: Mapped[Optional[str]] = mapped_column(String(1024))
    primary_language: Mapped[Optional[str]] = mapped_column(String(255))
    npi: Mapped[Optional[str]] = mapped_column(String(255))
    verified_npi: Mapped[Optional[str]] = mapped_column(String(255))

    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_super_admin: Mapped[Optional[bool]] = mapped_column(Boolean)
    system_tag: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    status: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(ProfileStatusEnum, name="profilestatusenum"), nullable=False
    )
    preferred_name: Mapped[Optional[str]] = mapped_column(String(255))
    default_theme: Mapped[Optional[str]] = mapped_column(String(255))

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id")
    )
    current_profile: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organization._id")
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="profiles")
    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="profiles"
    )
    status_history: Mapped[List["ProfileStatus"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    roles: Mapped[List["ProfileRole"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    locations: Mapped[List["ProfileLocation"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        back_populates="profile", cascade="all"
    )
    group_links: Mapped[List["ProfileGroup"]] = relationship(back_populates="profile")


class ProfileLocation(TableBase):
    """Stores device / geo information for a profile."""

    __tablename__ = "profile_location"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.profile._id"), nullable=False
    )
    app_name: Mapped[Optional[str]] = mapped_column(String(255))
    app_version: Mapped[Optional[str]] = mapped_column(String(15))
    device_id: Mapped[Optional[str]] = mapped_column(String(255))
    device_type: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(15))
    lat: Mapped[Optional[float]] = mapped_column()
    lng: Mapped[Optional[float]] = mapped_column()

    profile: Mapped["Profile"] = relationship(back_populates="locations")


class ProfileStatus(TableBase):
    """Audit log of profile status transitions."""

    __tablename__ = "profile_status"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.profile._id"), nullable=False
    )
    src_state: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(ProfileStatusEnum, name="profilestatusenum"), nullable=False
    )
    dst_state: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(ProfileStatusEnum, name="profilestatusenum"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(String(1024))

    profile: Mapped["Profile"] = relationship(back_populates="status_history")


class ProfileRole(TableBase):
    """Role assignments for a profile."""

    __tablename__ = "profile_role"

    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.profile._id")
    )
    role_key: Mapped[Optional[str]] = mapped_column(String(255))
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    role_source: Mapped[Optional[str]] = mapped_column(String(255))

    profile: Mapped[Optional["Profile"]] = relationship(back_populates="roles")
