"""
RFX Message Domain Type Definitions (Schema Layer)

This module mirrors the enums declared in ``rfx_message.types`` so we can
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
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    SYSTEM = "SYSTEM"


class ActionTypeEnum(Enum):
    HTTP = "HTTP"
    LINK = "LINK"


class HTTPMethodEnum(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PATCH = "PATCH"


class HTTPTargetEnum(Enum):
    BLANK = "BLANK"
    IFRAME = "IFRAME"


class TagGroupEnum(Enum):
    APPLICATION = "APPLICATION"
    FUNCTION = "FUNCTION"


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
