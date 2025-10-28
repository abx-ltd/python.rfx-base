from enum import Enum


class RFXDiscussStatusEnum(Enum):
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


class ActivityActionEnum(Enum):
    """Activity actions for logging ticket and Discuss-related activities"""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    COMMENT = "COMMENT"
    REPLY = "REPLY"
    EDIT_COMMENT = "EDIT_COMMENT"
    DELETE_COMMENT = "DELETE_COMMENT"
    ASSIGN = "ASSIGN"
    UNASSIGN = "UNASSIGN"
    CLOSE = "CLOSE"
    REOPEN = "REOPEN"
    ESCALATE = "ESCALATE"
    TRANSFER = "TRANSFER"
    RESOLVE = "RESOLVE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ARCHIVE = "ARCHIVE"
    VIEW = "VIEW"
    ATTACH = "ATTACH"
    DETACH = "DETACH"
