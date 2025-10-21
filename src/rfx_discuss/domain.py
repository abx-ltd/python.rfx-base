from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDiscussAggregate
from .state import RFXDiscussStateManager
from .policy import RFXDiscussPolicyManager
from . import config


class RFXDiscussDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXDiscussAggregate
    __statemgr__ = RFXDiscussStateManager
    __logstore__ = SQLDomainLogStore
    __policymgr__ = RFXDiscussPolicyManager




class CommentResponse(RFXDiscussDomain.Response):
    pass


class StatusResponse(RFXDiscussDomain.Response):
    pass


class StatusKeyResponse(RFXDiscussDomain.Response):
    pass


class StatusTransitionResponse(RFXDiscussDomain.Response):
    pass

class SyncTicketToLinearResponse(RFXDiscussDomain.Response):
    pass