"""
Notification Service Database Models

This module defines SQLAlchemy models for a comprehensive notification system that supports:
- Multi-channel notifications (Email, SMS, Push, Webhook)
- Provider management and configuration
- Delivery tracking and status
- Template support
- Retry mechanisms
"""
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.dialects import postgresql as pg
from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR

from . import config
from . import types


class NotifyConnector(SqlaDriver):
    """Database connector for the notification service."""
    assert config.DB_DSN, "[rfx_notify.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class NotifyBaseModel(NotifyConnector.__data_schema_base__, DomainSchema):
    """Base model class for all notification service models."""
    __abstract__ = True
    __table_args__ = {'schema': config.NOTIFY_SERVICE_SCHEMA}

    _realm = sa.Column(sa.String)


class Notification(NotifyBaseModel):
    """
    Core notification entity for tracking notifications sent through various channels.
    Supports Email, SMS, Push, Webhook, and In-app notifications.
    """

    __tablename__ = "notification"

    # Recipient and sender
    recipient_id = sa.Column(pg.UUID)  # User/entity receiving the notification
    sender_id = sa.Column(pg.UUID)     # User/entity sending (optional)

    # Channel and provider
    channel = sa.Column(
        sa.Enum(types.NotificationChannelEnum, name="notificationchannelenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )
    provider_id = sa.Column(pg.UUID, nullable=True)  # Reference to provider

    # Content
    subject = sa.Column(sa.String(512))
    body = sa.Column(sa.Text)
    content_type = sa.Column(
        sa.Enum(types.ContentTypeEnum, name="contenttypeenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.ContentTypeEnum.TEXT
    )

    # Delivery information
    recipient_address = sa.Column(sa.String(512))  # Email, phone number, device token, etc.

    # Status and tracking
    status = sa.Column(
        sa.Enum(types.NotificationStatusEnum, name="notificationstatusenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.NotificationStatusEnum.PENDING,
        nullable=False
    )
    priority = sa.Column(
        sa.Enum(types.NotificationPriorityEnum, name="notificationpriorityenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.NotificationPriorityEnum.NORMAL
    )

    # Timestamps
    scheduled_at = sa.Column(sa.DateTime(timezone=True))  # When to send (null = immediate)
    sent_at = sa.Column(sa.DateTime(timezone=True))
    delivered_at = sa.Column(sa.DateTime(timezone=True))
    failed_at = sa.Column(sa.DateTime(timezone=True))

    # Error tracking
    error_message = sa.Column(sa.Text)
    error_code = sa.Column(sa.String(64))
    retry_count = sa.Column(sa.Integer, default=0)
    max_retries = sa.Column(sa.Integer, default=3)

    # Template information
    template_key = sa.Column(sa.String(255))
    template_version = sa.Column(sa.Integer)
    template_data = sa.Column(pg.JSONB, default=dict)

    # Additional metadata
    meta = sa.Column(pg.JSONB, default=dict)
    tags = sa.Column(pg.ARRAY(sa.String))

    # External provider response
    provider_message_id = sa.Column(sa.String(512))  # ID from external provider
    provider_response = sa.Column(pg.JSONB, default=dict)


class NotificationProvider(NotifyBaseModel):
    """
    Provider configuration for external notification services.
    Supports multiple providers per channel with priority and fallback.
    """

    __tablename__ = "notification_provider"

    # Provider identity
    name = sa.Column(sa.String(255), nullable=False)
    provider_type = sa.Column(
        sa.Enum(types.ProviderTypeEnum, name="providertypeenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )
    channel = sa.Column(
        sa.Enum(types.NotificationChannelEnum, name="notificationchannelenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )

    # Configuration
    config = sa.Column(pg.JSONB, default=dict)  # Provider-specific config (API keys, endpoints, etc.)
    credentials = sa.Column(pg.JSONB, default=dict)  # Encrypted credentials

    # Status and priority
    status = sa.Column(
        sa.Enum(types.ProviderStatusEnum, name="providerstatusenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.ProviderStatusEnum.ACTIVE
    )
    priority = sa.Column(sa.Integer, default=100)  # Lower number = higher priority
    is_default = sa.Column(sa.Boolean, default=False)

    # Rate limiting
    rate_limit_per_minute = sa.Column(sa.Integer)
    rate_limit_per_hour = sa.Column(sa.Integer)
    rate_limit_per_day = sa.Column(sa.Integer)

    # Retry configuration
    retry_strategy = sa.Column(
        sa.Enum(types.RetryStrategyEnum, name="retrystrategyenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.RetryStrategyEnum.EXPONENTIAL
    )
    retry_delays = sa.Column(pg.ARRAY(sa.Integer), default=[60, 300, 900])  # Delays in seconds

    # Metadata
    description = sa.Column(sa.Text)
    meta = sa.Column(pg.JSONB, default=dict)

    # Tenant/scope (for multi-tenancy)
    tenant_id = sa.Column(pg.UUID)
    app_id = sa.Column(sa.String(64))


class NotificationDeliveryLog(NotifyBaseModel):
    """
    Detailed delivery attempt logs for notifications.
    Tracks each delivery attempt with provider responses.
    """

    __tablename__ = "notification_delivery_log"

    # References
    notification_id = sa.Column(pg.UUID, sa.ForeignKey(Notification._id), nullable=False)
    provider_id = sa.Column(pg.UUID, sa.ForeignKey(NotificationProvider._id))

    # Attempt information
    attempt_number = sa.Column(sa.Integer, nullable=False)
    attempted_at = sa.Column(sa.DateTime(timezone=True), default=datetime.utcnow)

    # Result
    status = sa.Column(
        sa.Enum(types.NotificationStatusEnum, name="notificationstatusenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )
    status_code = sa.Column(sa.String(64))  # HTTP status, SMTP code, etc.

    # Response details
    response = sa.Column(pg.JSONB, default=dict)
    error_message = sa.Column(sa.Text)

    # Timing
    duration_ms = sa.Column(sa.Integer)  # How long the attempt took


class NotificationTemplate(NotifyBaseModel):
    """
    Templates for notifications across different channels.
    Similar to message templates but for external channels.
    """

    __tablename__ = "notification_template"

    # Template identity
    key = sa.Column(sa.String(255), nullable=False)
    version = sa.Column(sa.Integer, default=1)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)

    # Channel and locale
    channel = sa.Column(
        sa.Enum(types.NotificationChannelEnum, name="notificationchannelenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )
    locale = sa.Column(sa.String(10), default="en")

    # Content
    subject_template = sa.Column(sa.String(512))  # For email
    body_template = sa.Column(sa.Text, nullable=False)
    content_type = sa.Column(
        sa.Enum(types.ContentTypeEnum, name="contenttypeenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        default=types.ContentTypeEnum.TEXT
    )

    # Template engine
    engine = sa.Column(sa.String(32), default='jinja2')
    variables_schema = sa.Column(pg.JSONB, default=dict)

    # Status
    is_active = sa.Column(sa.Boolean, default=True)

    # Tenant/scope
    tenant_id = sa.Column(pg.UUID)
    app_id = sa.Column(sa.String(64))

    __table_args__ = (
        sa.UniqueConstraint('tenant_id', 'app_id', 'key', 'version',
                            'channel', 'locale', name='uq_notify_template_scope'),
        {'schema': config.NOTIFY_SERVICE_SCHEMA}
    )


class NotificationPreference(NotifyBaseModel):
    """
    User preferences for notification channels and types.
    Allows users to control how they receive notifications.
    """

    __tablename__ = "notification_preference"

    # User reference
    user_id = sa.Column(pg.UUID, nullable=False)

    # Channel preferences
    channel = sa.Column(
        sa.Enum(types.NotificationChannelEnum, name="notificationchannelenum",
                schema=config.NOTIFY_SERVICE_SCHEMA),
        nullable=False
    )
    enabled = sa.Column(sa.Boolean, default=True)

    # Contact information
    email_address = sa.Column(sa.String(255))
    phone_number = sa.Column(sa.String(20))
    device_token = sa.Column(sa.String(512))  # For push notifications

    # Preferences
    opt_in = sa.Column(sa.Boolean, default=True)
    frequency_limit = sa.Column(pg.JSONB, default=dict)
    preferences = sa.Column(pg.JSONB, default=dict)  # Additional user preferences

    # Quiet hours
    quiet_hours_start = sa.Column(sa.Time)
    quiet_hours_end = sa.Column(sa.Time)
    quiet_hours_timezone = sa.Column(sa.String(64))

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'channel', name='uq_user_channel_preference'),
        {'schema': config.NOTIFY_SERVICE_SCHEMA}
    )
