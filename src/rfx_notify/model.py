"""
Notification Service Database Models

This module defines SQLAlchemy models for a comprehensive notification system that supports:
- Multi-channel notifications (Email, SMS, Push, Webhook)
- Provider management and configuration
- Delivery tracking and status
- Template support
- Retry mechanisms
"""
from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR

from . import config as notify_config
from . import types


class NotifyConnector(SqlaDriver):
    """Database connector for the notification service."""
    assert notify_config.DB_DSN, "[rfx_notify.DB_DSN] not set."

    __db_dsn__ = notify_config.DB_DSN
