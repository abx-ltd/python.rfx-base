"""
QR Domain ORM Mapping
=====================

Schema-only models for QR codes tied to transactions. These tables capture QR
creation, scan events, redemption state, and external references.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import QRCodeStatusEnum, QRRedemptionStatusEnum, QRScanResultEnum


class QRCode(TableBase):
    """Core QR code stored in ``rfx_qr.qr_code``."""

    __tablename__ = "qr_code"

    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    qr_code: Mapped[Optional[str]] = mapped_column(String(512))

    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[QRCodeStatusEnum] = mapped_column(
        SQLEnum(QRCodeStatusEnum, name="qrcodestatusenum", schema=SCHEMA),
        nullable=False,
        default=QRCodeStatusEnum.CREATED,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    scans: Mapped[List["QRScan"]] = relationship(
        back_populates="qr_code", cascade="all, delete-orphan"
    )
    redemptions: Mapped[List["QRRedemption"]] = relationship(
        back_populates="qr_code", cascade="all, delete-orphan"
    )
    references: Mapped[List["QRReference"]] = relationship(
        back_populates="qr_code", cascade="all, delete-orphan"
    )


class QRScan(TableBase):
    """Scan events recorded in ``rfx_qr.qr_scan``."""

    __tablename__ = "qr_scan"

    qr_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.qr_code._id"), nullable=False
    )
    scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scanner_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    location: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[Optional[QRScanResultEnum]] = mapped_column(
        SQLEnum(QRScanResultEnum, name="qrscanresultenum", schema=SCHEMA)
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(64))

    qr_code: Mapped["QRCode"] = relationship(back_populates="scans")


class QRRedemption(TableBase):
    """Redemption records stored in ``rfx_qr.qr_redemption``."""

    __tablename__ = "qr_redemption"

    qr_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.qr_code._id"), nullable=False
    )
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    redeemer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    status: Mapped[QRRedemptionStatusEnum] = mapped_column(
        SQLEnum(QRRedemptionStatusEnum, name="qrredemptionstatusenum", schema=SCHEMA),
        nullable=False,
        default=QRRedemptionStatusEnum.PENDING,
    )

    qr_code: Mapped["QRCode"] = relationship(back_populates="redemptions")


class QRReference(TableBase):
    """External references for QR codes stored in ``rfx_qr.qr_reference``."""

    __tablename__ = "qr_reference"

    qr_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.qr_code._id"), nullable=False
    )
    ref_type: Mapped[Optional[str]] = mapped_column(String(64))
    ref_value: Mapped[Optional[str]] = mapped_column(String(255))

    qr_code: Mapped["QRCode"] = relationship(back_populates="references")
