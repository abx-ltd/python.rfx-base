"""
RFX QR Domain Type Definitions (Schema Layer)

Enum definitions used by the QR schema models for Alembic and metadata.
"""

from enum import Enum


class QRCodeStatusEnum(Enum):
    CREATED = "CREATED"
    ISSUED = "ISSUED"
    SCANNED = "SCANNED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REDEEMED = "REDEEMED"


class QRScanResultEnum(Enum):
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    ERROR = "ERROR"


class QRRedemptionStatusEnum(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
