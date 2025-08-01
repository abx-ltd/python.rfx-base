from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import CPOPortalAggregate
from .state import CPOPortalStateManager
# from .policy import CPOPortalPolicyManager


class CPOPortalDomain(Domain):
    __namespace__ = 'cpo-portal'
    __aggregate__ = CPOPortalAggregate
    __statemgr__ = CPOPortalStateManager
    __logstore__ = SQLDomainLogStore
    # __policymgr__   = CPOPortalPolicyManager



class TicketResponse(CPOPortalDomain.Response):
    pass


class TagResponse(CPOPortalDomain.Response):
    pass