"""
Generic Template Schema
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, Boolean, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

from . import TableBase, SCHEMA


class Template(TableBase):
    """Generic template definition."""

    __tablename__ = "template"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "app_id", "key", "version", "channel", "locale",
            name="uq_template_scope"
        ),
        {"schema": SCHEMA}
    )

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    locale: Mapped[str] = mapped_column(String(10), default="en")
    channel: Mapped[Optional[str]] = mapped_column(String(32))

    # Template content
    body: Mapped[str] = mapped_column(Text, nullable=False)

    engine: Mapped[str] = mapped_column(String(32), default="jinja2")
    variables_schema: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Domain-specific metadata (e.g., subject templates for notifications)
    meta_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    app_id: Mapped[Optional[str]] = mapped_column(String(64))


class TemplateRenderLog(TableBase):
    """Log of template rendering events."""

    __tablename__ = "template_render_log"
    __table_args__ = {"schema": SCHEMA}

    template_key: Mapped[str] = mapped_column(String(255))
    template_version: Mapped[int] = mapped_column(Integer)

    # Scope/Context
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    app_id: Mapped[Optional[str]] = mapped_column(String(64))
    locale: Mapped[Optional[str]] = mapped_column(String(10))
    channel: Mapped[Optional[str]] = mapped_column(String(32))

    # Parameters
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)

    rendered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
