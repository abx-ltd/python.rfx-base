"""
RFX Notify Domain Type Definitions (Schema Layer)

This module mirrors the enums declared in ``rfx_notify.types`` so we can
reference them inside the schema package (Alembic, metadata reflection)
without importing the full service layer.
"""

from enum import Enum


class NotificationChannelEnum(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"
    INAPP = "INAPP"


class ProviderTypeEnum(Enum):
    SMTP = "SMTP"
    SENDGRID = "SENDGRID"
    SES = "SES"
    TWILIO = "TWILIO"
    SNS = "SNS"
    FIREBASE = "FIREBASE"
    MQTT = "MQTT"
    CUSTOM = "CUSTOM"


class NotificationStatusEnum(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    BOUNCED = "BOUNCED"


class NotificationPriorityEnum(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ContentTypeEnum(Enum):
    TEXT = "TEXT"
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"

