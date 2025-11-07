"""
Media Service ORM Mapping (Schema Layer)
========================================

Schema-only SQLAlchemy models mirroring the runtime definitions in
``lib.fluvius.media.model``. These models give Alembic and metadata tools
visibility into the media tables without loading the actual service package.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, CHAR, DateTime, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA
from .types import FsSpecCompressionMethod


class MediaEntry(TableBase):
    """Binary objects stored in the media service."""

    __tablename__ = "media-entry"

    filename: Mapped[str] = mapped_column(String(1024), nullable=False)
    filehash: Mapped[Optional[str]] = mapped_column(CHAR(64))
    filemime: Mapped[Optional[str]] = mapped_column(String(256))
    fskey: Mapped[Optional[str]] = mapped_column(String(24))
    length: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    fspath: Mapped[Optional[str]] = mapped_column(String(1024))
    compress: Mapped[Optional[FsSpecCompressionMethod]] = mapped_column(
        SQLEnum(FsSpecCompressionMethod, name="fsspeccompressionmethod", schema=SCHEMA)
    )
    resource: Mapped[Optional[str]] = mapped_column(String(24))
    resource__id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True))
    resource_sid: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True))
    resource_iid: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True))
    xattrs: Mapped[Optional[str]] = mapped_column(String(256))
    cdn_exp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cdn_url: Mapped[Optional[str]] = mapped_column(String(1024))
