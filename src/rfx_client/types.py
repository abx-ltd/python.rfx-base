from enum import Enum


class CPOPortalStatusEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class PriorityEnum(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRIVIAL = "TRIVIAL"


class SyncStatusEnum(Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class AvailabilityEnum(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class EntityTypeEnum(Enum):
    PROJECT = "project"
    TICKET = "ticket"
    WORKFLOW = "workflow"


class WorkflowStatusEnum(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class NotificationTypeEnum(Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    MILESTONE_DUE = "MILESTONE_DUE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class ContactMethodEnum(Enum):
    MESSAGE = "MESSAGE"
    PHONE_CALL = "PHONE_CALL"
    MEETING = "MEETING"


class ActivityActionEnum(Enum):
    """Activity actions for logging project-related activities"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    ASSIGN = "ASSIGN"
    UNASSIGN = "UNASSIGN"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SUBMIT = "SUBMIT"
    COMPLETE = "COMPLETE"
    CANCEL = "CANCEL"
    PROMOTE = "PROMOTE"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"

class InquiryStatusEnum(Enum):
    """ Inquiry status enum """
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    DISCUSSION = "DISCUSSION"
    CLOSED = "CLOSED"