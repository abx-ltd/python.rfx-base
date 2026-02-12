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
