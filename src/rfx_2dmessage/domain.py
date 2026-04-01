from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFX2DMessageAggregate
from .state import RFX2DMessageStateManager
from .policy import RFX2DMessagePolicyManager
from . import config


class RFX2DMessageDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFX2DMessageAggregate
    __statemgr__ = RFX2DMessageStateManager
    __logstore__ = SQLDomainLogStore
    # __policymgr__ = RFX2DMessagePolicyManager


class MessageResponse(RFX2DMessageDomain.Response):
    pass


class BoxResponse(RFX2DMessageDomain.Response):
    pass