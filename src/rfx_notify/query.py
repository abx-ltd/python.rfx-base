from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField, BooleanField, DatetimeField, UUIDField, EnumField, IntegerField, JSONField
)
from typing import Optional, List

from .state import NotifyStateManager
from .domain import NotifyServiceDomain
from .types import (
    NotificationChannelEnum,
    NotificationStatusEnum,
    NotificationPriorityEnum,
    ProviderTypeEnum,
    ProviderStatusEnum,
    ContentTypeEnum
)
from . import logger


class NotifyServiceQueryManager(DomainQueryManager):
    __data_manager__ = NotifyStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = NotifyServiceDomain.Meta.prefix
        tags = NotifyServiceDomain.Meta.tags


resource = NotifyServiceQueryManager.register_resource
endpoint = NotifyServiceQueryManager.register_endpoint


@resource('notifications')
class NotificationQuery(DomainQueryResource):
    """Query resource for notifications."""

    @classmethod
    def base_query(cls, context, scope):
        # Default: show notifications for the current user
        # Can be overridden by admins to see all notifications
        filters = {}

        if hasattr(context, 'user') and context.user:
            filters['recipient_id'] = context.user._id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "notification"

        default_order = ("-_created",)

    # Fields
    recipient_id: UUID_TYPE = UUIDField("Recipient ID")
    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")
    channel: NotificationChannelEnum = EnumField("Channel", enum=NotificationChannelEnum)
    provider_id: Optional[UUID_TYPE] = UUIDField("Provider ID")

    subject: Optional[str] = StringField("Subject")
    body: str = StringField("Body")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)
    recipient_address: str = StringField("Recipient Address")

    status: NotificationStatusEnum = EnumField("Status", enum=NotificationStatusEnum)
    priority: NotificationPriorityEnum = EnumField("Priority", enum=NotificationPriorityEnum)

    scheduled_at: Optional[str] = DatetimeField("Scheduled At")
    sent_at: Optional[str] = DatetimeField("Sent At")
    delivered_at: Optional[str] = DatetimeField("Delivered At")
    failed_at: Optional[str] = DatetimeField("Failed At")

    error_message: Optional[str] = StringField("Error Message")
    error_code: Optional[str] = StringField("Error Code")
    retry_count: int = IntegerField("Retry Count", default=0)
    max_retries: int = IntegerField("Max Retries", default=3)

    template_key: Optional[str] = StringField("Template Key")
    template_version: Optional[int] = IntegerField("Template Version")
    template_data: dict = JSONField("Template Data")

    meta: dict = JSONField("Metadata")
    tags: Optional[List[str]] = StringField("Tags")

    provider_message_id: Optional[str] = StringField("Provider Message ID")
    provider_response: dict = JSONField("Provider Response")


@resource('notification-providers')
class NotificationProviderQuery(DomainQueryResource):
    """Query resource for notification providers."""

    @classmethod
    def base_query(cls, context, scope):
        # Providers are usually scoped by tenant/app
        filters = {}

        if hasattr(context, 'tenant_id') and context.tenant_id:
            filters['tenant_id'] = context.tenant_id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "notification_provider"
        policy_required = True  # Admins only

        default_order = ("priority", "name")

    # Fields
    name: str = StringField("Name")
    provider_type: ProviderTypeEnum = EnumField("Provider Type", enum=ProviderTypeEnum)
    channel: NotificationChannelEnum = EnumField("Channel", enum=NotificationChannelEnum)

    config: dict = JSONField("Configuration")
    # Note: credentials are typically not exposed in queries for security

    status: ProviderStatusEnum = EnumField("Status", enum=ProviderStatusEnum)
    priority: int = IntegerField("Priority")
    is_default: bool = BooleanField("Is Default", default=False)

    rate_limit_per_minute: Optional[int] = IntegerField("Rate Limit Per Minute")
    rate_limit_per_hour: Optional[int] = IntegerField("Rate Limit Per Hour")
    rate_limit_per_day: Optional[int] = IntegerField("Rate Limit Per Day")

    description: Optional[str] = StringField("Description")
    meta: dict = JSONField("Metadata")

    tenant_id: Optional[UUID_TYPE] = UUIDField("Tenant ID")
    app_id: Optional[str] = StringField("App ID")


@resource('notification-delivery-logs')
class NotificationDeliveryLogQuery(DomainQueryResource):
    """Query resource for notification delivery logs."""

    @classmethod
    def base_query(cls, context, scope):
        # Admins can see all logs
        filters = {}

        # If a notification_id is provided in scope, filter by it
        if scope and hasattr(scope, 'notification_id'):
            filters['notification_id'] = scope.notification_id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "notification_delivery_log"
        policy_required = True  # Admins only

        default_order = ("-attempted_at",)

    # Fields
    notification_id: UUID_TYPE = UUIDField("Notification ID")
    provider_id: Optional[UUID_TYPE] = UUIDField("Provider ID")

    attempt_number: int = IntegerField("Attempt Number")
    attempted_at: str = DatetimeField("Attempted At")

    status: NotificationStatusEnum = EnumField("Status", enum=NotificationStatusEnum)
    status_code: Optional[str] = StringField("Status Code")

    response: dict = JSONField("Response")
    error_message: Optional[str] = StringField("Error Message")

    duration_ms: Optional[int] = IntegerField("Duration (ms)")


@resource('notification-preferences')
class NotificationPreferenceQuery(DomainQueryResource):
    """Query resource for user notification preferences."""

    @classmethod
    def base_query(cls, context, scope):
        # Users can only see their own preferences
        filters = {}

        if hasattr(context, 'user') and context.user:
            filters['user_id'] = context.user._id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "notification_preference"

        default_order = ("channel",)

    # Fields
    user_id: UUID_TYPE = UUIDField("User ID")
    channel: NotificationChannelEnum = EnumField("Channel", enum=NotificationChannelEnum)
    enabled: bool = BooleanField("Enabled", default=True)

    email_address: Optional[str] = StringField("Email Address")
    phone_number: Optional[str] = StringField("Phone Number")
    device_token: Optional[str] = StringField("Device Token")

    opt_in: bool = BooleanField("Opt In", default=True)
    frequency_limit: dict = JSONField("Frequency Limit")
    preferences: dict = JSONField("Preferences")

    quiet_hours_start: Optional[str] = StringField("Quiet Hours Start")
    quiet_hours_end: Optional[str] = StringField("Quiet Hours End")
    quiet_hours_timezone: Optional[str] = StringField("Quiet Hours Timezone")


@resource('notification-templates')
class NotificationTemplateQuery(DomainQueryResource):
    """Query resource for notification templates."""

    @classmethod
    def base_query(cls, context, scope):
        # Templates are scoped by tenant/app
        filters = {}

        if hasattr(context, 'tenant_id') and context.tenant_id:
            filters['tenant_id'] = context.tenant_id

        if hasattr(context, 'app_id') and context.app_id:
            filters['app_id'] = context.app_id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "notification_template"
        policy_required = True  # Admins only

        default_order = ("key", "-version")

    # Fields
    key: str = StringField("Template Key")
    version: int = IntegerField("Version")
    name: Optional[str] = StringField("Name")
    description: Optional[str] = StringField("Description")

    channel: NotificationChannelEnum = EnumField("Channel", enum=NotificationChannelEnum)
    locale: str = StringField("Locale", default="en")

    subject_template: Optional[str] = StringField("Subject Template")
    body_template: str = StringField("Body Template")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)

    engine: str = StringField("Engine", default="jinja2")
    variables_schema: dict = JSONField("Variables Schema")

    is_active: bool = BooleanField("Is Active", default=True)

    tenant_id: Optional[UUID_TYPE] = UUIDField("Tenant ID")
    app_id: Optional[str] = StringField("App ID")
