from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDiscussionAggregate
from .state import RFXDiscussionStateManager
# from .policy import RFXDiscussionAggregatePolicyManager


class RFXDiscussionDomain(Domain):
    __namespace__ = 'rfx-discussion'
    __aggregate__ = RFXDiscussionAggregate
    __statemgr__ = RFXDiscussionStateManager
    __logstore__ = SQLDomainLogStore
    # __policymgr__   = RFXDiscussionPolicyManager


class TicketResponse(RFXDiscussionDomain.Response):
    pass


class TicketTypeResponse(RFXDiscussionDomain.Response):
    pass


class TagResponse(RFXDiscussionDomain.Response):
    pass


class CommentResponse(RFXDiscussionDomain.Response):
    pass
