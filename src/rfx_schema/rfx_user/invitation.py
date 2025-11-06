"""
Invitation Aggregate ORM Mapping
================================

Handles invitations issued from organizations to users or profiles along with
status change history.

| Table            | Purpose                                 | Key Relationships                      |
| ---------------- | --------------------------------------- | -------------------------------------- |
| invitation       | Invitation record linking sender/target | FK → organization, user, profile       |
| invitation_status| Audit log of invitation transitions     | FK → invitation                        |
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rfx_user.types import InvitationStatusEnum

from . import Base

if TYPE_CHECKING:  # pragma: no cover
    from .organization import Organization
    from .user import User
    from .profile import Profile


class Invitation(Base):
    """Organization invitation workflow entry."""

    __tablename__ = "invitation"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.organization._id"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id"), nullable=False
    )
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.profile._id")
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.user._id")
    )

    email: Mapped[Optional[str]] = mapped_column(String(255))
    token: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[InvitationStatusEnum] = mapped_column(
        SQLEnum(InvitationStatusEnum, name="invitation_status_enum"), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    message: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[int]] = mapped_column(Integer)

    organization: Mapped["Organization"] = relationship(back_populates="invitations")
    sender: Mapped["User"] = relationship(
        back_populates="sent_invitations", foreign_keys=[sender_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        back_populates="received_invitations", foreign_keys=[user_id]
    )
    profile: Mapped[Optional["Profile"]] = relationship(back_populates="invitations")
    status_history: Mapped[List["InvitationStatus"]] = relationship(
        back_populates="invitation", cascade="all, delete-orphan"
    )


class InvitationStatus(Base):
    """Status transitions for an invitation."""

    __tablename__ = "invitation_status"

    invitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.invitation._id"), nullable=False
    )
    src_state: Mapped[InvitationStatusEnum] = mapped_column(
        SQLEnum(InvitationStatusEnum, name="invitation_status_enum"), nullable=False
    )
    dst_state: Mapped[InvitationStatusEnum] = mapped_column(
        SQLEnum(InvitationStatusEnum, name="invitation_status_enum"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(Text)

    invitation: Mapped["Invitation"] = relationship(back_populates="status_history")
