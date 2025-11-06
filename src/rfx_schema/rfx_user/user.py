"""
User Aggregate ORM Mapping
==========================

The user aggregate drives identity, authentication, and audit tracking. The
tables model the user account plus all supporting artifacts (identity
providers, sessions, verification history, and required actions).

| Table           | Purpose                                | Key Relationships                                 |
| --------------- | -------------------------------------- | ------------------------------------------------- |
| user            | Primary user account record            | 1 → N identities, sessions, actions, statuses     |
| user_identity   | External identity providers            | N → 1 user                                        |
| user_session    | Active authentication sessions         | N → 1 user, optional identity                     |
| user_status     | Audit of status transitions            | N → 1 user                                        |
| user_verification| Verification metadata (email/phone)   | N → 1 user, optional identity                     |
| user_action     | Required actions from SSO/Keycloak     | N → 1 user, optional identity, FK → ref__action   |
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rfx_user.types import (
    UserActionStatusEnum,
    UserSourceEnum,
    UserStatusEnum,
)

from . import Base

if TYPE_CHECKING:  # pragma: no cover
    from .profile import Profile
    from .invitation import Invitation


class User(Base):
    """Primary user account stored in the `rfx_user.user` table."""

    __tablename__ = "user"

    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Name components
    name__family: Mapped[Optional[str]] = mapped_column(String(1024))
    name__given: Mapped[Optional[str]] = mapped_column(String(1024))
    name__middle: Mapped[Optional[str]] = mapped_column(String(1024))
    name__prefix: Mapped[Optional[str]] = mapped_column(String(1024))
    name__suffix: Mapped[Optional[str]] = mapped_column(String(1024))

    # Telecom
    telecom__email: Mapped[Optional[str]] = mapped_column(String(1024))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(1024))

    # Identity
    username: Mapped[Optional[str]] = mapped_column(String(1024))
    verified_email: Mapped[Optional[str]] = mapped_column(String(1024))
    verified_phone: Mapped[Optional[str]] = mapped_column(String(1024))
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(UserStatusEnum, name="user_status_enum"), nullable=False
    )
    realm_access: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    resource_access: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    last_verified_request: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    identities: Mapped[List["UserIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["UserStatus"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    verifications: Mapped[List["UserVerification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    actions: Mapped[List["UserAction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profiles: Mapped[List["Profile"]] = relationship(
        back_populates="user", cascade="all"
    )
    sent_invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="sender",
        cascade="all",
        foreign_keys="Invitation.sender_id",
    )
    received_invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="user",
        cascade="all",
        foreign_keys="Invitation.user_id",
    )


class UserIdentity(Base):
    """External identity providers linked to a user."""

    __tablename__ = "user_identity"

    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    telecom__email: Mapped[Optional[str]] = mapped_column(String(255))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(255))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="identities")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="identity")
    verifications: Mapped[List["UserVerification"]] = relationship(
        back_populates="identity"
    )
    actions: Mapped[List["UserAction"]] = relationship(back_populates="identity")


class UserSession(Base):
    """Authentication sessions tied to a user."""

    __tablename__ = "user_session"

    source: Mapped[Optional[UserSourceEnum]] = mapped_column(
        SQLEnum(UserSourceEnum, name="user_source_enum"), nullable=True
    )
    telecom__email: Mapped[Optional[str]] = mapped_column(String(255))

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id")
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user_identity._id")
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="sessions")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="sessions"
    )


class UserStatus(Base):
    """Audit log of user status transitions."""

    __tablename__ = "user_status"

    src_state: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(UserStatusEnum, name="user_status_enum"), nullable=False
    )
    dst_state: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(UserStatusEnum, name="user_status_enum"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(String(1024))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="status_history")


class UserVerification(Base):
    """Email and phone verification tracking for a user."""

    __tablename__ = "user_verification"

    verification: Mapped[str] = mapped_column(String(1024), nullable=False)
    last_sent_email: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id"), nullable=False
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user_identity._id")
    )

    user: Mapped["User"] = relationship(back_populates="verifications")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="verifications"
    )


class UserAction(Base):
    """Required actions associated with a user (e.g. reset password)."""

    __tablename__ = "user_action"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("rfx_user.ref__action.key")
    )
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[UserActionStatusEnum] = mapped_column(
        SQLEnum(UserActionStatusEnum, name="user_action_status_enum"),
        nullable=False,
        server_default=text(f"'{UserActionStatusEnum.PENDING.value}'"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id"), nullable=False
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user_identity._id")
    )

    user: Mapped["User"] = relationship(back_populates="actions")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="actions"
    )
