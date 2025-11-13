"""
RFX Client Domain Type Definitions (Schema Layer)

This module mirrors the enums declared in ``rfx_client.types`` for schema layer usage.
"""

from enum import Enum


class ProjectStatusEnum(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class WorkPackageStatusEnum(Enum):
    TODO = "TODO"
    PENDING = "PENDING"
    DONE = "DONE"


class MemberRoleEnum(Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class TransactionTypeEnum(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    REFUND = "REFUND"


class BillingCycleEnum(Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ProjectVisibilityEnum(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    INTERNAL = "INTERNAL"


class PriorityEnum(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRIVIAL = "TRIVIAL"


class AvailabilityEnum(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ContactMethodEnum(Enum):
    MESSAGE = "MESSAGE"
    PHONE_CALL = "PHONE_CALL"
    MEETING = "MEETING"


class EntityTypeEnum(Enum):
    PROJECT = "PROJECT"
    TICKET = "TICKET"
    WORKFLOW = "WORKFLOW"


class NotificationTypeEnum(Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    MILESTONE_DUE = "MILESTONE_DUE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class SyncStatusEnum(Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class WorkflowStatusEnum(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PurchaseStatusEnum(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
