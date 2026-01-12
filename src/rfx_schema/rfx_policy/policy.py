"""
Policy Service ORM Mapping (Schema Layer)
=========================================

Schema-only SQLAlchemy models mirroring ``src/rfx_policy/model.py`` so Alembic
and metadata consumers can access the policy tables without importing the
runtime package.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from . import TableBase, SCHEMA
from .types import (
    PolicyCQRSEnum,
    PolicyEffectEnum,
    PolicyKindEnum,
    PolicyScopeEnum,
    PolicyStatusEnum,
)


class Policy(TableBase):
    """Top-level policy definition."""

    __tablename__ = "policy"
    __table_args__ = (
        Index("policy_key_unique", "key", unique=True),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[Optional[int]] = mapped_column(Integer)
    effect: Mapped[Optional[PolicyEffectEnum]] = mapped_column(
        SQLEnum(PolicyEffectEnum, name="policyeffectenum", schema=SCHEMA)
    )
    status: Mapped[Optional[PolicyStatusEnum]] = mapped_column(
        SQLEnum(PolicyStatusEnum, name="policystatusenum", schema=SCHEMA)
    )
    scope: Mapped[Optional[PolicyScopeEnum]] = mapped_column(
        SQLEnum(PolicyScopeEnum, name="policyscopeenum", schema=SCHEMA)
    )
    kind: Mapped[Optional[PolicyKindEnum]] = mapped_column(
        SQLEnum(PolicyKindEnum, name="policykindenum", schema=SCHEMA)
    )

    resources: Mapped[List["PolicyResource"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    roles: Mapped[List["PolicyRole"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class PolicyResource(TableBase):
    """Individual resource/action binding for a policy."""

    __tablename__ = "policy_resource"

    key: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[Optional[int]] = mapped_column(Integer)
    effect: Mapped[Optional[PolicyEffectEnum]] = mapped_column(
        SQLEnum(PolicyEffectEnum, name="policyeffectenum", schema=SCHEMA)
    )
    status: Mapped[Optional[PolicyStatusEnum]] = mapped_column(
        SQLEnum(PolicyStatusEnum, name="policystatusenum", schema=SCHEMA)
    )
    scope: Mapped[Optional[PolicyScopeEnum]] = mapped_column(
        SQLEnum(PolicyScopeEnum, name="policyscopeenum", schema=SCHEMA)
    )
    kind: Mapped[Optional[PolicyKindEnum]] = mapped_column(
        SQLEnum(PolicyKindEnum, name="policykindenum", schema=SCHEMA)
    )
    cqrs: Mapped[Optional[PolicyCQRSEnum]] = mapped_column(
        SQLEnum(PolicyCQRSEnum, name="policycqrsenum", schema=SCHEMA)
    )
    domain: Mapped[Optional[str]] = mapped_column(String(255))
    action: Mapped[Optional[str]] = mapped_column(String(255))
    resource: Mapped[Optional[str]] = mapped_column(String(255))
    policy_key: Mapped[str] = mapped_column(
        String(255), ForeignKey(f"{SCHEMA}.policy.key"), nullable=False
    )
    meta: Mapped[str] = mapped_column(Text, server_default=text("''"), nullable=False)
    policy: Mapped["Policy"] = relationship(back_populates="resources")


class PolicyRole(TableBase):
    """Associates policies with roles."""

    __tablename__ = "policy_role"

    policy_key: Mapped[str] = mapped_column(
        String(255), ForeignKey(f"{SCHEMA}.policy.key"), nullable=False
    )
    role_key: Mapped[Optional[str]] = mapped_column(String(255))
    policy: Mapped["Policy"] = relationship(back_populates="roles")
    scope: Mapped[str] = mapped_column(String(255))
