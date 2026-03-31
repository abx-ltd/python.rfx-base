from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import uuid




from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    BigInteger,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import INTERVAL, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import (
    RecordStatusEnum,
    ServiceCategoryEnum,
)

class ServiceCategory(TableBase):

    __tablename__ = "service_category"

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ServiceCategoryEnum] = mapped_column(SQLEnum(ServiceCategoryEnum), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RecordStatusEnum] = mapped_column(SQLEnum(RecordStatusEnum), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))


class Supplier(TableBase):

    __tablename__ = "supplier"

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)

    tax_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    status: Mapped[RecordStatusEnum] = mapped_column(SQLEnum(RecordStatusEnum), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

class SupplierService(TableBase):

    __tablename__ = "supplier_service"

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.supplier._id"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.service_category._id"), nullable=False)
    status: Mapped[RecordStatusEnum] = mapped_column(SQLEnum(RecordStatusEnum), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
