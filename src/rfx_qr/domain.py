from fluvius.domain import Domain, SQLDomainLogStore

from .state import QRStateManager
from .aggregate import QRAggregate
from ._meta import config


class QRServiceDomain(Domain):
    """Domain for the QR service, encapsulating QR-related operations."""

    __namespace__ = config.QR_DOMAIN_NAMESPACE
    __aggregate__ = QRAggregate
    __statemgr__ = QRStateManager
    __logstore__ = SQLDomainLogStore


class QRServiceResponse(QRServiceDomain.Response):
    """Response class for QR service operations."""
    pass

class QRServiceMessage(QRServiceDomain.Message):
    """Message class for QR service operations."""
    pass
