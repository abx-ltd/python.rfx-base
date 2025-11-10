"""
Template Models for Message Service (Schema Layer)
==================================================

Schema-friendly replicas of the message template tables so Alembic and other
metadata consumers can reason about them without loading the runtime package.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import RenderStrategyEnum, TemplateStatusEnum


class MessageTemplate(TableBase):
    """Template definitions stored in ``rfx_message.message_template``."""

    __tablename__ = "message_template"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "app_id",
            "key",
            "version",
            "locale",
            "channel",
            name="uq_template_scope",
        ),
        {"schema": SCHEMA},
    )

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    channel: Mapped[Optional[str]] = mapped_column(String(32))

    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    app_id: Mapped[Optional[str]] = mapped_column(String(64))

    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    engine: Mapped[Optional[str]] = mapped_column(String(32), default="jinja2")
    context: Mapped[Optional[str]] = mapped_column(Text)

    variables_schema: Mapped[dict] = mapped_column(JSONB, default=dict)

    render_strategy: Mapped[Optional[RenderStrategyEnum]] = mapped_column(
        SQLEnum(RenderStrategyEnum, name="renderstrategyenum", schema=SCHEMA)
    )
    status: Mapped[TemplateStatusEnum] = mapped_column(
        SQLEnum(TemplateStatusEnum, name="templatestatusenum", schema=SCHEMA),
        default=TemplateStatusEnum.DRAFT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TemplateRenderCache(TableBase):
    """Cache table for compiled template payloads."""

    __tablename__ = "template_render_cache"
    __table_args__ = (
        UniqueConstraint(
            "template_key",
            "template_version",
            "locale",
            "channel",
            name="uq_cache_key",
        ),
        {"schema": SCHEMA},
    )

    template_key: Mapped[str] = mapped_column(String(255), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, default=1)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    channel: Mapped[Optional[str]] = mapped_column(String(32))

    compiled_template: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
