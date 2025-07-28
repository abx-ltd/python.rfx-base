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


# Specific response types for different commands
class ProjectResponse(CPOPortalDomain.Response):
    pass


class WorkPackageResponse(CPOPortalDomain.Response):
    pass


class TicketResponse(CPOPortalDomain.Response):
    pass


class ProjectTicketResponse(CPOPortalDomain.Response):
    pass


class NotificationResponse(CPOPortalDomain.Response):
    pass


class CreditBreakdownResponse(CPOPortalDomain.Response):
    pass


class ResourceUploadResponse(CPOPortalDomain.Response):
    pass


class SyncResultResponse(CPOPortalDomain.Response):
    pass
