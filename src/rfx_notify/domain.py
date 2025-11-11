from fluvius.domain import Domain, SQLDomainLogStore

from .state import NotifyStateManager
from .aggregate import NotifyAggregate
from ._meta import config


class RFXNotifyServiceDomain(Domain):
    """Domain for the notification service, encapsulating notification-related operations."""

    __namespace__ = config.NAMESPACE
    __aggregate__ = NotifyAggregate
    __statemgr__ = NotifyStateManager
    __logstore__ = SQLDomainLogStore


class NotifyServiceResponse(RFXNotifyServiceDomain.Response):
    """Response class for notification service operations."""
    pass


class NotifyServiceMessage(RFXNotifyServiceDomain.Message):
    """Message class for notification service operations."""
    pass
