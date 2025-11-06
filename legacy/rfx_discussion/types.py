from enum import Enum


class RFXDiscussionStatus(Enum):
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


class ActivityAction(Enum):
    """Activity actions for logging ticket and discussion-related activities"""
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
