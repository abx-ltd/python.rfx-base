from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import CPOPortalAggregate
from .state import CPOPortalStateManager
# from .policy import CPOPortalPolicyManager
from . import config


class CPOPortalDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = CPOPortalAggregate
    __statemgr__ = CPOPortalStateManager
    __logstore__ = SQLDomainLogStore
    # __policymgr__   = CPOPortalPolicyManager


# Specific response types for different commands

# Promotion related responses

class PromotionResponse(CPOPortalDomain.Response):
    pass


# Project related responses
class ProjectResponse(CPOPortalDomain.Response):
    pass


class ProjectCategoryResponse(CPOPortalDomain.Response):
    pass


class ProjectTicketResponse(CPOPortalDomain.Response):
    pass


class ResourceUploadResponse(CPOPortalDomain.Response):
    pass


class ProjectBDMContactResponse(CPOPortalDomain.Response):
    pass


class ProjectMilestoneResponse(CPOPortalDomain.Response):
    pass


class ProjectWorkPackageResponse(CPOPortalDomain.Response):
    pass


class ProjectWorkItemResponse(CPOPortalDomain.Response):
    pass


# Work Package related responses


class WorkPackageResponse(CPOPortalDomain.Response):
    pass


class WorkPackageTypeResponse(CPOPortalDomain.Response):
    pass


class WorkPackageDeliverableResponse(CPOPortalDomain.Response):
    pass


# Work Item related responses

class WorkItemResponse(CPOPortalDomain.Response):
    pass


class WorkItemDeliverableResponse(CPOPortalDomain.Response):
    pass


class WorkItemTypeResponse(CPOPortalDomain.Response):
    pass


# Notification related responses

class NotificationResponse(CPOPortalDomain.Response):
    pass


# class CreditBreakdownResponse(CPOPortalDomain.Response):
#     pass


# Integration related responses

class SyncResultResponse(CPOPortalDomain.Response):
    pass
