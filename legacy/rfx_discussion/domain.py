from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDiscussionAggregate
from .state import RFXDiscussionStateManager
from .policy import RFXDiscussionPolicyManager
from . import config


class RFXDiscussionDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXDiscussionAggregate
    __statemgr__ = RFXDiscussionStateManager
    __logstore__ = SQLDomainLogStore
    __policymgr__ = RFXDiscussionPolicyManager


class TicketResponse(RFXDiscussionDomain.Response):
    pass


class TicketTypeResponse(RFXDiscussionDomain.Response):
    pass


class TagResponse(RFXDiscussionDomain.Response):
    pass


class CommentResponse(RFXDiscussionDomain.Response):
    pass


class StatusResponse(RFXDiscussionDomain.Response):
    pass


class StatusKeyResponse(RFXDiscussionDomain.Response):
    pass


class StatusTransitionResponse(RFXDiscussionDomain.Response):
    pass

class SyncTicketToLinearResponse(RFXDiscussionDomain.Response):
    pass