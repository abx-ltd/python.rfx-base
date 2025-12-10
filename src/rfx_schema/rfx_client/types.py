"""
RFX Client Domain Type Definitions (Schema Layer)

This module mirrors the enums declared in ``rfx_client.types`` for schema layer usage.
"""

from enum import Enum


class ProjectStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class WorkPackageStatusEnum(str, Enum):
    TODO = "TODO"
    PENDING = "PENDING"
    DONE = "DONE"


class MemberRoleEnum(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class TransactionTypeEnum(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    REFUND = "REFUND"


class BillingCycleEnum(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ProjectVisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    INTERNAL = "INTERNAL"


class PriorityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRIVIAL = "TRIVIAL"


class AvailabilityEnum(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ContactMethodEnum(str, Enum):
    MESSAGE = "MESSAGE"
    PHONE_CALL = "PHONE_CALL"
    MEETING = "MEETING"


class EntityTypeEnum(str, Enum):
    PROJECT = "PROJECT"
    TICKET = "TICKET"
    WORKFLOW = "WORKFLOW"


class NotificationTypeEnum(str, Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    MILESTONE_DUE = "MILESTONE_DUE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class SyncStatusEnum(str, Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class WorkflowStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PurchaseStatusEnum(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    
class InquiryStatusEnum(str, Enum):
    """ Inquiry status enum """
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    DISCUSSION = "DISCUSSION"
    CLOSED = "CLOSED"
