"""
QR generator utilities for VietQR payloads and images.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import Field
from fluvius.data import DataModel


class QRBaseConfig(DataModel):
    """Base VietQR data (consumer/account identity and metadata)."""

    bin_id: str = Field(min_length=1)
    consumer_id: str = Field(min_length=1)
    service_code: str = Field(default="ACCOUNT")
    point_of_initiation_method: str = Field(default="DYNAMIC")
    transaction_currency: int = Field(default=704)
    store_label: Optional[str] = None
    reference_label: Optional[str] = None


class QRTransactionInput(DataModel):
    """Transaction-specific VietQR data (amount, payer info)."""

    transaction_amount: Optional[float] = None
    purpose_of_transaction: Optional[str] = None
    bill_number: Optional[str] = None
    mobile_number: Optional[str] = None
    customer_label: Optional[str] = None


class QRGenerator:
    """Generate VietQR payloads and images using napas-qr-python."""

    __qr_config__: Optional[Dict[str, Any]] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is not None:
            self.__qr_config__ = config

    def code(self, transaction: dict) -> str:
        """Return the VietQR payload string."""
        transaction_input = QRTransactionInput(**transaction)
        qr_pay = self._build_qr_pay(transaction=transaction_input)
        return qr_pay.code

    def _build_qr_pay(self, transaction: Optional[QRTransactionInput] = None):
        if not self.__qr_config__:
            raise ValueError("QR base config is not set")
        base_config = self._resolve_base_config(self.__qr_config__)
        payload = dict(base_config.model_dump(exclude_none=True))
        if transaction:
            payload.update(transaction.model_dump(exclude_none=True))
        try:
            from qr_pay import QRPay
        except ImportError as exc:
            raise ImportError(
                "napas-qr-python is required. Install with `pip install napas-qr-python`."
            ) from exc
        return QRPay(**payload)

    @staticmethod
    def _resolve_base_config(
        config: Dict[str, Any]
    ) -> QRBaseConfig:
        return QRBaseConfig(**config)
