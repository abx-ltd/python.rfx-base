"""
RFX Template Domain
"""
from fluvius.domain import Domain, SQLDomainLogStore
from ._meta import config
from .aggregate import TemplateAggregate
from .state import TemplateStateManager


class TemplateServiceDomain(Domain):
    """Domain for managing templates."""

    __namespace__ = config.NAMESPACE
    __aggregate__ = TemplateAggregate
    __statemgr__ = TemplateStateManager
    __logstore__ = SQLDomainLogStore

class TemplateServiceResponse(TemplateServiceDomain.Response):
    """Response class for template service operations."""
    pass


class TemplateServiceMessage(TemplateServiceDomain.Message):
    """Message class for template service operations."""
    pass
