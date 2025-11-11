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
    ProviderTypeEnum,
)


class SendNotificationPayload(DataModel):
    """Payload for creating and sending a notification."""

    channel: NotificationChannelEnum = Field(
        ..., description="Channel to deliver the notification (EMAIL, SMS, etc.)"
    )
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
    provider_type: Optional[ProviderTypeEnum] = Field(
        None, description="Specific provider type to force for delivery."
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


__all__ = [
    "SendNotificationPayload",
    "NotificationStatusUpdatePayload",
    "NotificationPreferencePayload",
    "NotificationTemplatePayload",
]
