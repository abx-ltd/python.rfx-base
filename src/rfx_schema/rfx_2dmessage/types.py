"""
RFX Message Domain Type Definitions (Schema Layer)

This module mirrors the enums declared in ``rfx_2dmessage.types`` so we can
reference them inside the schema package (Alembic, metadata reflection)
without importing the full service layer.
"""

from enum import Enum


class ContentTypeEnum(Enum):
    TEXT = "TEXT"
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    XML = "XML"


class PriorityLevelEnum(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MessageTypeEnum(Enum):
    NOTIFICATION = "NOTIFICATION"
    ALERT = "ALERT"
    REMINDER = "REMINDER"
    SYSTEM = "SYSTEM"
    USER = "USER"


class DeliveryStatusEnum(Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class DirectionTypeEnum(Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class ExecutionModeEnum(Enum):
    API = "API"
    EMBED = "EMBED"

class ActionTypeEnum(Enum):
    FORM = "FORM"
    ATOMIC = "ATOMIC"
    EMBEDDED = "EMBEDDED"

class ActionExecutionStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CANCEL = "CANCEL"


class HTTPMethodEnum(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PATCH = "PATCH"


class HTTPTargetEnum(Enum):
    BLANK = "BLANK"
    IFRAME = "IFRAME"


class BoxTypeEnum(Enum):
    GROUP = "GROUP"
    SINGLE = "SINGLE"


class RenderStatusEnum(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLIENT_RENDERING = "CLIENT_RENDERING"
    FAILED = "FAILED"


class TemplateStatusEnum(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class RenderStrategyEnum(Enum):
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    CACHED = "CACHED"
    STATIC = "STATIC"


class ProcessingModeEnum(Enum):
    SYNC = "SYNC"
    ASYNC = "ASYNC"
    IMMEDIATE = "IMMEDIATE"


class MessageCategoryEnum(Enum):
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    INFORMATION = "INFORMATION"


class MailBoxTypeEnum(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    NOTIFICATION = "NOTIFICATION"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    SYSTEM = "SYSTEM"
    WEBHOOK = "WEBHOOK"
    WORK = "WORK"

class MailBoxMessageStatusTypeEnum(Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    DONE = "DONE"
    
class MailBoxMemberRoleEnum(Enum):
    OWNER = "OWNER"
    CONTRIBUTOR = "CONTRIBUTOR"
    VIEWER = "VIEWER"


class MediaTypeEnum(Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    ARCHIVE = "ARCHIVE"
    OTHER = "OTHER"