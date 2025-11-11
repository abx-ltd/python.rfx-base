"""
Payload definitions for notification commands.
"""
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from fluvius.data import DataModel, Field, UUID_TYPE
from pydantic import validator

from .types import (
    ContentTypeEnum,
    NotificationChannelEnum,
    NotificationPriorityEnum,
    NotificationStatusEnum,
    ProviderStatusEnum,
    ProviderTypeEnum,
    RetryStrategyEnum,
)


class SendNotificationPayload(DataModel):
    """Payload for creating and sending a notification."""

    channel: NotificationChannelEnum = Field( ..., description="Channel to deliver the notification (EMAIL, SMS, etc.)")
    recipient_address: str = Field(
        ..., description="Destination address such as email, phone number, or device token."
    )
    subject: Optional[str] = Field(
        None, description="Subject or title (used by email-like channels)."
    )
    body: Optional[str] = Field(
        None, description="Raw body content when not using templates."
    )
    content_type: ContentTypeEnum = Field(
        ContentTypeEnum.TEXT, description="Content type for the body or rendered template."
    )
    recipient_id: Optional[UUID_TYPE] = Field(
        None, description="Recipient entity identifier (user/contact id)."
    )
    sender_id: Optional[UUID_TYPE] = Field(
        None, description="Sender entity identifier."
    )
    provider_id: Optional[UUID_TYPE] = Field(
        None, description="Specific provider to force for delivery."
    )
    priority: NotificationPriorityEnum = Field(
        NotificationPriorityEnum.NORMAL, description="Delivery priority."
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="Optional ISO timestamp for scheduled delivery."
    )
    template_key: Optional[str] = Field(
        None, description="Template key to render content from."
    )
    template_version: Optional[int] = Field(
        None, description="Specific template version to use."
    )
    template_data: Dict[str, Any] = Field(
        default_factory=dict, description="Variables passed to the template renderer."
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata such as from_email, cc, bcc, media_url, etc.",
    )
    tags: List[str] = Field(
        default_factory=list, description="Optional tags for classification/search."
    )
    max_retries: int = Field(
        3, description="Maximum number of retry attempts allowed if delivery fails."
    )

    @validator("channel", pre=True)
    def normalize_channel(cls, value):
        if isinstance(value, str):
            value = value.upper()
            return NotificationChannelEnum(value)
        return value

    @validator("content_type", pre=True)
    def normalize_content_type(cls, value):
        if isinstance(value, str):
            value = value.upper()
            return ContentTypeEnum(value)
        return value

    @validator("priority", pre=True)
    def normalize_priority(cls, value):
        if isinstance(value, str):
            value = value.upper()
            return NotificationPriorityEnum(value)
        return value


class NotificationStatusUpdatePayload(DataModel):
    """Payload for updating notification delivery status."""

    status: NotificationStatusEnum = Field(
        ..., description="New status to apply to the notification."
    )
    error_message: Optional[str] = Field(
        None, description="Error message when marking the notification as failed."
    )
    provider_message_id: Optional[str] = Field(
        None, description="Provider message identifier associated with the update."
    )
    provider_response: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw payload or metadata received from the provider.",
    )


class NotificationProviderPayload(DataModel):
    """Payload for creating a notification provider definition."""

    name: str = Field(..., description="Display name for the provider.")
    provider_type: ProviderTypeEnum = Field(
        ..., description="Provider implementation type (SMTP, SENDGRID, TWILIO, etc.)."
    )
    channel: NotificationChannelEnum = Field(
        ..., description="Channel served by this provider."
    )
    status: ProviderStatusEnum = Field(
        ProviderStatusEnum.ACTIVE, description="Initial provider status."
    )
    priority: int = Field(
        100, description="Lower numbers represent higher priority when selecting providers."
    )
    is_default: bool = Field(
        False, description="Whether this provider should be selected by default for the channel."
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider configuration block (endpoints, options, etc.)."
    )
    credentials: Dict[str, Any] = Field(
        default_factory=dict, description="Credential payload (API keys, secrets, etc.)."
    )
    rate_limit_per_minute: Optional[int] = Field(
        None, description="Optional provider-specific per-minute rate limit."
    )
    rate_limit_per_hour: Optional[int] = Field(
        None, description="Optional provider-specific per-hour rate limit."
    )
    rate_limit_per_day: Optional[int] = Field(
        None, description="Optional provider-specific per-day rate limit."
    )
    retry_strategy: RetryStrategyEnum = Field(
        RetryStrategyEnum.EXPONENTIAL, description="Retry strategy to apply on failure."
    )
    retry_delays: List[int] = Field(
        default_factory=lambda: [60, 300, 900],
        description="Retry delay schedule in seconds.",
    )
    description: Optional[str] = Field(
        None, description="Human friendly description of the provider."
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata stored with the provider."
    )
    tenant_id: Optional[UUID_TYPE] = Field(
        None, description="Tenant identifier for multi-tenant scoping."
    )
    app_id: Optional[str] = Field(
        None, description="Application identifier for multi-app scoping."
    )


class NotificationProviderUpdatePayload(DataModel):
    """Payload for updating an existing notification provider."""

    name: Optional[str] = Field(None, description="Updated provider display name.")
    status: Optional[ProviderStatusEnum] = Field(
        None, description="Updated provider status."
    )
    priority: Optional[int] = Field(
        None, description="Updated priority for provider selection."
    )
    is_default: Optional[bool] = Field(
        None, description="Whether the provider should become the default."
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Replacement configuration block."
    )
    credentials: Optional[Dict[str, Any]] = Field(
        None, description="Replacement credential payload."
    )
    rate_limit_per_minute: Optional[int] = Field(
        None, description="Updated per-minute rate limit."
    )
    rate_limit_per_hour: Optional[int] = Field(
        None, description="Updated per-hour rate limit."
    )
    rate_limit_per_day: Optional[int] = Field(
        None, description="Updated per-day rate limit."
    )
    retry_strategy: Optional[RetryStrategyEnum] = Field(
        None, description="Updated retry strategy."
    )
    retry_delays: Optional[List[int]] = Field(
        None, description="Updated retry delay schedule in seconds."
    )
    description: Optional[str] = Field(
        None, description="Updated description of the provider."
    )
    meta: Optional[Dict[str, Any]] = Field(
        None, description="Updated metadata block."
    )
    tenant_id: Optional[UUID_TYPE] = Field(
        None, description="Updated tenant identifier."
    )
    app_id: Optional[str] = Field(
        None, description="Updated application identifier."
    )


class ChangeProviderStatusPayload(DataModel):
    """Payload for toggling provider status."""

    status: ProviderStatusEnum = Field(
        ..., description="New status value (ACTIVE, INACTIVE, DISABLED, etc.)."
    )


class NotificationPreferencePayload(DataModel):
    """Payload for updating user notification preferences."""

    channel: NotificationChannelEnum = Field(
        ..., description="Channel that the preference applies to."
    )
    enabled: bool = Field(True, description="Whether notifications are enabled.")
    email_address: Optional[str] = Field(
        None, description="Preferred email address for the user."
    )
    phone_number: Optional[str] = Field(
        None, description="Preferred phone number for SMS/MMS."
    )
    device_token: Optional[str] = Field(
        None, description="Device token for push notifications."
    )
    opt_in: bool = Field(True, description="Whether the user opted into the channel.")
    frequency_limit: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom frequency limit configuration per channel.",
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict, description="Additional structured preference data."
    )
    quiet_hours_start: Optional[time] = Field(
        None, description="Start of quiet hours (local time)."
    )
    quiet_hours_end: Optional[time] = Field(
        None, description="End of quiet hours (local time)."
    )
    quiet_hours_timezone: Optional[str] = Field(
        None, description="Timezone identifier for quiet hours."
    )


class NotificationTemplatePayload(DataModel):
    """Payload for creating notification templates."""

    key: str = Field(..., description="Template key identifier.")
    channel: NotificationChannelEnum = Field(
        ..., description="Channel the template is intended for."
    )
    body_template: str = Field(
        ..., description="Template body definition (Jinja, text, etc.)."
    )
    subject_template: Optional[str] = Field(
        None, description="Optional subject template for email-like channels."
    )
    name: Optional[str] = Field(None, description="Friendly template name.")
    engine: str = Field("jinja2", description="Template engine (jinja2, text, static).")
    locale: str = Field("en", description="Locale code for the template.")
    content_type: ContentTypeEnum = Field(
        ContentTypeEnum.TEXT, description="Rendered content type."
    )
    tenant_id: Optional[UUID_TYPE] = Field(
        None, description="Tenant identifier for scoped templates."
    )
    app_id: Optional[str] = Field(
        None, description="Application identifier for scoped templates."
    )
    variables_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Optional schema describing required variables."
    )
