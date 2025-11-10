from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, SCHEMA
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
        SQLEnum(ProfileStatusEnum, name="profilestatusenum"), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<UserProfileView(_id={self._id}, username={self.username}, "
            f"status={self.status})>"
        )
