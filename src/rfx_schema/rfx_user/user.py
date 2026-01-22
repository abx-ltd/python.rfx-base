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

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import from local types to avoid rfx_user module initialization
from .types import (
    UserActionStatusEnum,
    UserSourceEnum,
    UserStatusEnum,
)

from . import TableBase, SCHEMA

if TYPE_CHECKING:  # pragma: no cover
    from .profile import Profile
    from .invitation import Invitation


class User(TableBase):
    """Primary user account stored in the `rfx_user.user` table."""

    __tablename__ = "user"
    __ts_index__ = ["name__family", "name__given", "telecom__email", "telecom__phone", "username"]

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
        SQLEnum(
            UserStatusEnum,
            name="userstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
        default=UserStatusEnum.NEW,
        server_default=text(f"'{UserStatusEnum.NEW.value}'"),
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
    _created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=text("now()")
    )

class GuestUser(TableBase):
    """Guest user account stored in the `rfx_user.guest_user` table."""

    __tablename__ = "guest_user"

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

class GuestVerification(TableBase):
    """Guest verification codes stored in the `rfx_user.guest_verification` table."""

    __tablename__ = "guest_verification"

    guest_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("rfx_user.guest_user._id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Reference to guest user if they've signed in before"
    )
    method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'email'"),
        comment="Verification method: 'email' or 'sms'"
    )
    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Email address or phone number where code was sent"
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when code was successfully verified"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the request"
    )
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of verification attempts for this code"
    )


class UserIdentity(TableBase):
    """External identity providers linked to a user."""

    __tablename__ = "user_identity"

    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    telecom__email: Mapped[Optional[str]] = mapped_column(String(255))
    telecom__phone: Mapped[Optional[str]] = mapped_column(String(255))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="identities")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="identity")
    verifications: Mapped[List["UserVerification"]] = relationship(
        back_populates="identity"
    )
    actions: Mapped[List["UserAction"]] = relationship(back_populates="identity")


class UserSession(TableBase):
    """Authentication sessions tied to a user."""

    __tablename__ = "user_session"

    source: Mapped[Optional[UserSourceEnum]] = mapped_column(
        SQLEnum(
            UserSourceEnum,
            name="usersourceenum",
            schema=SCHEMA,
        ),
        nullable=True,
    )
    telecom__email: Mapped[Optional[str]] = mapped_column(String(255))

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id")
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user_identity._id")
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="sessions")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="sessions"
    )


class UserStatus(TableBase):
    """Audit log of user status transitions."""

    __tablename__ = "user_status"

    src_state: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(
            UserStatusEnum,
            name="userstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    dst_state: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(
            UserStatusEnum,
            name="userstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(String(1024))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="status_history")


class UserVerification(TableBase):
    """Email and phone verification tracking for a user."""

    __tablename__ = "user_verification"

    verification: Mapped[str] = mapped_column(String(1024), nullable=False)
    last_sent_email: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id"), nullable=False
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user_identity._id")
    )

    user: Mapped["User"] = relationship(back_populates="verifications")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="verifications"
    )


class UserAction(TableBase):
    """Required actions associated with a user (e.g. reset password)."""

    __tablename__ = "user_action"

    _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(f"{SCHEMA}.ref__action.key")
    )
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[UserActionStatusEnum] = mapped_column(
        SQLEnum(
            UserActionStatusEnum,
            name="useractionstatusenum",
            schema=SCHEMA,
        ),
        nullable=False,
        server_default=text(f"'{UserActionStatusEnum.PENDING.value}'"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user._id"), nullable=False
    )
    user_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.user_identity._id")
    )

    user: Mapped["User"] = relationship(back_populates="actions")
    identity: Mapped[Optional["UserIdentity"]] = relationship(
        back_populates="actions"
    )
