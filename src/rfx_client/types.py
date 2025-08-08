from enum import Enum


class CPOPortalStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class Priority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRIVIAL = "TRIVIAL"


class SyncStatus(Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class Availability(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class EntityType(Enum):
    PROJECT = "project"
    TICKET = "ticket"
    WORKFLOW = "workflow"


class WorkflowStatus(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class NotificationType(Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    MILESTONE_DUE = "MILESTONE_DUE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class ContactMethod(Enum):
    MESSAGE = "MESSAGE"
    PHONE_CALL = "PHONE_CALL"
    MEETING = "MEETING"


class WorkPackageItemStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
