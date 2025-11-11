"""
RFX Notify Domain Type Definitions

Enum definitions for notification channels, providers, and delivery status
used throughout the notification system.
"""

from enum import Enum


class NotificationChannelEnum(Enum):
    """
    Notification channel types for different delivery methods.
    Determines how notifications are sent to recipients.
    """
    EMAIL = "EMAIL"           # Email notification
    SMS = "SMS"               # SMS text message
    PUSH = "PUSH"             # Push notification
    WEBHOOK = "WEBHOOK"       # Webhook callback
    INAPP = "INAPP"           # In-app notification (via MQTT)


class ProviderTypeEnum(Enum):
    """
    Provider types for external notification services.
    """
    SMTP = "SMTP"             # SMTP email provider
    SENDGRID = "SENDGRID"     # SendGrid email service
    SES = "SES"               # AWS SES
    TWILIO = "TWILIO"         # Twilio SMS service
    SNS = "SNS"               # AWS SNS
    FIREBASE = "FIREBASE"     # Firebase Cloud Messaging
    MQTT = "MQTT"             # MQTT broker
    CUSTOM = "CUSTOM"         # Custom provider


class NotificationStatusEnum(Enum):
    """
    Notification delivery status for tracking delivery progress.
    """
    PENDING = "PENDING"           # Queued for delivery
    PROCESSING = "PROCESSING"     # Being processed
    SENT = "SENT"                 # Successfully sent to provider
    DELIVERED = "DELIVERED"       # Confirmed delivery (if available)
    FAILED = "FAILED"             # Delivery failed
    REJECTED = "REJECTED"         # Rejected by provider
    BOUNCED = "BOUNCED"           # Bounced (email specific)


class NotificationPriorityEnum(Enum):
    """
    Notification priority levels for delivery urgency.
    """
    LOW = "LOW"               # Low priority, can be batched
    NORMAL = "NORMAL"         # Normal priority
    HIGH = "HIGH"             # High priority, immediate delivery
    URGENT = "URGENT"         # Urgent, bypass rate limits if possible


class ProviderStatusEnum(Enum):
    """
    Provider availability status.
    """
    ACTIVE = "ACTIVE"         # Provider is active and available
    INACTIVE = "INACTIVE"     # Provider is inactive
    DISABLED = "DISABLED"     # Provider is disabled
    ERROR = "ERROR"           # Provider has errors


class ContentTypeEnum(Enum):
    """
    Content type for notification body.
    """
    TEXT = "TEXT"             # Plain text
    HTML = "HTML"             # HTML content
    MARKDOWN = "MARKDOWN"     # Markdown content
    JSON = "JSON"             # JSON payload


class RetryStrategyEnum(Enum):
    """
    Retry strategies for failed notifications.
    """
    NONE = "NONE"                     # No retry
    LINEAR = "LINEAR"                 # Fixed interval retry
    EXPONENTIAL = "EXPONENTIAL"       # Exponential backoff
    FIBONACCI = "FIBONACCI"           # Fibonacci backoff
