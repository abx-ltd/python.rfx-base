"""
Group Aggregate ORM Mapping
===========================

Security groups provide many-to-many associations between profiles and logical
group containers for permission management.

| Table         | Purpose                         | Key Relationships            |
| ------------- | ------------------------------- | ---------------------------- |
| group         | Group definition                | N ↔ N profiles via bridge    |
| profile_group | Bridge linking profile to group | FK → group, FK → profile     |
"""

from __future__ import annotations

import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:  # pragma: no cover
    from .profile import Profile


class Group(Base):
    """Security group definition."""

    __tablename__ = "group"

    _txt: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    description: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(String(1024))
    resource: Mapped[Optional[str]] = mapped_column(String(255))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    profiles: Mapped[List["ProfileGroup"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class ProfileGroup(Base):
    """Bridge table linking profiles to groups."""

    __tablename__ = "profile_group"

    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.group._id")
    )
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfx_user.profile._id")
    )

    group: Mapped[Optional["Group"]] = relationship(back_populates="profiles")
    profile: Mapped[Optional["Profile"]] = relationship(back_populates="group_links")
