from fluvius.domain import Domain, SQLDomainLogStore

from .state import MessageStateManager
from .aggregate import MessageAggregate
from . import config


class MessageServiceDomain(Domain):
    """Domain for the message service, encapsulating message-related operations."""

    __namespace__ = config.NAMESPACE
    __aggregate__ = MessageAggregate
    __statemgr__ = MessageStateManager
    __logstore__ = SQLDomainLogStore
    # __policymgr__ = None


class MessageServiceResponse(MessageServiceDomain.Response):
    """Response class for message service operations."""
    pass


class MessageServiceMessage(MessageServiceDomain.Message):
    """Message class for message service operations."""
    pass
