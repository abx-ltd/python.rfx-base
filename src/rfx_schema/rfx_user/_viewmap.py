
from __future__ import annotations
from fluvius.casbin import PolicySchema

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, PolicyBase, SCHEMA, POLICY_SCHEMA
from .types import ProfileStatusEnum


class UserProfileView(Base):
    """
    ORM mapping for the materialized `_profile` view that powers read-heavy
    profile queries. The view mirrors the `profile` table while exposing a
    stable surface for downstream consumers.
    """

    __tablename__ = "_profile"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

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
    expiration_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
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

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    current_profile: Mapped[bool] = mapped_column(Boolean, nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    preferred_name: Mapped[Optional[str]] = mapped_column(String(255))
    default_theme: Mapped[Optional[str]] = mapped_column(String(255))

    _realm: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(
            ProfileStatusEnum,
            name="profilestatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<UserProfileView(_id={self._id}, username={self.username}, "
            f"status={self.status})>"
        )


class ProfileListView(Base):
    """
    ORM mapping for the materialized `_profile_list` view that powers
    read-heavy profile list queries. The view mirrors a subset of the
    `profile` table while exposing a stable surface for downstream consumers.
    """

    __tablename__ = "_profile_list"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    name__family: Mapped[Optional[str]] = mapped_column(String(1024))
    name__given: Mapped[Optional[str]] = mapped_column(String(1024))
    preferred_name: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__email: Mapped[Optional[str]] = mapped_column(String(1024))
    realm: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(
            ProfileStatusEnum,
            name="profilestatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    organization_name: Mapped[Optional[str]] = mapped_column(String(255))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    current_profile: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ProfileListView(_id={self._id}, username={self.username}, "
            f"status={self.status})>"
        )


class OrgMemberView(Base):
    """
    ORM mapping for the materialized `_org_member` view that powers
    read-heavy organization member queries. The view mirrors a subset of the
    `profile` table while exposing a stable surface for downstream consumers.
    """

    __tablename__ = "_org_member"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    organization_name: Mapped[Optional[str]] = mapped_column(String(255))
    name__given: Mapped[Optional[str]] = mapped_column(String(1024))
    name__middle: Mapped[Optional[str]] = mapped_column(String(1024))
    name__family: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__email: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(1024))
    profile_status: Mapped[ProfileStatusEnum] = mapped_column(
        SQLEnum(
            ProfileStatusEnum,
            name="profilestatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    profile_role: Mapped[Optional[str]] = mapped_column(String(255))
    policy_count: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return (
            f"<OrgMemberView(profile_id={self._id}, user_id={self.user_id}, "
            f"organization_id={self.organization_id})>"
        )


class PolicyUserProfileView(PolicyBase, PolicySchema):
    """
    ORM mapping for the `_policy__user_profile` view used to materialize Casbin
    policy tuples for the user-profile domain.
    """
    __tablename__ = "_policy__user_profile"
    __table_args__ = {"schema": POLICY_SCHEMA, "info": {"is_view": True}}


class PolicyIDMProfileView(PolicyBase, PolicySchema):
    """
    ORM mapping for the `_policy__idm_profile` view used for IDM profile access
    policy evaluation.
    """
    __tablename__ = "_policy__idm_profile"
    __table_args__ = {"schema": POLICY_SCHEMA, "info": {"is_view": True}}
