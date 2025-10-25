from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXClientAggregate
from .state import RFXClientStateManager
from .policy import RFXClientPolicyManager
from . import config


class RFXClientDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXClientAggregate
    __statemgr__ = RFXClientStateManager
    __logstore__ = SQLDomainLogStore
    __policymgr__   = RFXClientPolicyManager


# Specific response types for different commands

# Promotion related responses

class PromotionResponse(RFXClientDomain.Response):
    pass


# Project related responses
class ProjectResponse(RFXClientDomain.Response):
    pass


class ProjectCategoryResponse(RFXClientDomain.Response):
    pass


class ProjectTicketResponse(RFXClientDomain.Response):
    pass


class ResourceUploadResponse(RFXClientDomain.Response):
    pass


class ProjectBDMContactResponse(RFXClientDomain.Response):
    pass


class ProjectMilestoneResponse(RFXClientDomain.Response):
    pass


class ProjectWorkPackageResponse(RFXClientDomain.Response):
    pass


class ProjectWorkItemResponse(RFXClientDomain.Response):
    pass


# Work Package related responses


class WorkPackageResponse(RFXClientDomain.Response):
    pass


class WorkPackageTypeResponse(RFXClientDomain.Response):
    pass


class WorkPackageDeliverableResponse(RFXClientDomain.Response):
    pass


# Work Item related responses

class WorkItemResponse(RFXClientDomain.Response):
    pass


class WorkItemDeliverableResponse(RFXClientDomain.Response):
    pass


class WorkItemTypeResponse(RFXClientDomain.Response):
    pass


# Notification related responses

class NotificationResponse(RFXClientDomain.Response):
    pass


# class CreditBreakdownResponse(CPOPortalDomain.Response):
#     pass


# Integration related responses

class SyncResultResponse(RFXClientDomain.Response):
    pass


class CreditUsageSummaryResponse(RFXClientDomain.Response):
    pass

class SyncProjectToLinearResponse(RFXClientDomain.Response):
    pass

class ProjectIntegrationResponse(RFXClientDomain.Response):
    pass


#======= Ticket Responses ========
class TicketResponse(RFXClientDomain.Response):
    pass


class TicketTypeResponse(RFXClientDomain.Response):
    pass


class TagResponse(RFXClientDomain.Response):
    pass


class CommentResponse(RFXClientDomain.Response):
    pass


