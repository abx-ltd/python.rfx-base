from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField,
    BooleanField,
    DatetimeField,
    UUIDField,
    EnumField,
    ArrayField,
    IntegerField,
    JSONField,
)
from typing import Optional, List

from .state import MessageStateManager
from .domain import RFXMessageServiceDomain
from .types import (
    PriorityLevelEnum,
    ContentTypeEnum,
    MessageTypeEnum,
    RenderStrategyEnum,
    MessageCategoryEnum,
    BoxTypeEnum,
    DirectionTypeEnum,
)
from . import scope


class RFXMessageServiceQueryManager(DomainQueryManager):
    __data_manager__ = MessageStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXMessageServiceDomain.Meta.prefix
        tags = RFXMessageServiceDomain.Meta.tags


resource = RFXMessageServiceQueryManager.register_resource
endpoint = RFXMessageServiceQueryManager.register_endpoint


# class ResourceScope(BaseModel):
#     resource: str
#     resource_id: str


class TemplateScope(BaseModel):
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None
    locale: Optional[str] = None
    channel: Optional[str] = None


@resource("message-template")
class TemplateQuery(DomainQueryResource):
    """Query resource for message templates."""

    @classmethod
    def base_query(cls, context, scope):
        # Templates are typically scoped by tenant/app
        filters = {}

        if hasattr(context, "tenant_id") and context.tenant_id:
            filters["tenant_id"] = context.tenant_id

        if hasattr(context, "app_id") and context.app_id:
            filters["app_id"] = context.app_id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "message_template"
        resource = "message_template"
        policy_required = "id"
        scope_optional = TemplateScope

        default_order = ("key", "-version")

    # Template identity
    # id: UUID_TYPE = UUIDField("Template ID")
    key: str = StringField("Template Key")
    version: int = IntegerField("Version")
    name: str = StringField("Template Name")
    # Template content
    engine: str = StringField("Template Engine")
    body: str = StringField("Template Body")
    description: Optional[str] = StringField("Description")
    # Scoping
    locale: str = StringField("Locale")
    channel: Optional[str] = StringField("Channel")
    tenant_id: Optional[UUID_TYPE] = UUIDField("Tenant ID")
    app_id: Optional[str] = StringField("App ID")
    # Configuration
    render_strategy: Optional[RenderStrategyEnum] = EnumField(
        "Render Strategy", enum=RenderStrategyEnum
    )
    variables_schema: dict = JSONField("Variables Schema")
    sample_data: dict = JSONField("Sample Data")
    # Status
    status: str = StringField("Status")
    is_active: bool = BooleanField("Is Active")
    # Audit
    created_by: Optional[UUID_TYPE] = UUIDField("Created By")
    updated_by: Optional[UUID_TYPE] = UUIDField("Updated By")


# INBOX, OUTBOX
@resource("message-inbox")
class MessageInboxQuery(DomainQueryResource):
    """Query resource for message inbox."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "root_type": "RECIPIENT",
            "box_key": "inbox",
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_box"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    # Fields mapped from _message_box view
    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: Optional[bool] = BooleanField("Is Expirable")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: Optional[MessageCategoryEnum] = EnumField(
        "Category", enum=MessageCategoryEnum
    )
    is_read: Optional[bool] = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    box_key: Optional[str] = StringField("Box Key")
    box_name: Optional[str] = StringField("Box Name")
    box_type_enum: Optional[BoxTypeEnum] = EnumField("Box Type", enum=BoxTypeEnum)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    message_count: Optional[int] = IntegerField("Message Count")
    root_type: str = StringField("Root Type")


@resource("message-outbox")
class MessageOutboxQuery(DomainQueryResource):
    """Query resource for message outbox."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "root_type": "SENDER",
            "box_key": "outbox",
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_box"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: Optional[bool] = BooleanField("Is Expirable")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: Optional[MessageCategoryEnum] = EnumField(
        "Category", enum=MessageCategoryEnum
    )
    is_read: Optional[bool] = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    box_key: Optional[str] = StringField("Box Key")
    box_name: Optional[str] = StringField("Box Name")
    box_type_enum: Optional[BoxTypeEnum] = EnumField("Box Type", enum=BoxTypeEnum)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    message_count: Optional[int] = IntegerField("Message Count")
    root_type: str = StringField("Root Type")


@resource("message-archived")
class MessageArchivedQuery(DomainQueryResource):
    """Query resource for message archived."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "box_key": "archived",
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_box"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: Optional[bool] = BooleanField("Is Expirable")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: Optional[MessageCategoryEnum] = EnumField(
        "Category", enum=MessageCategoryEnum
    )
    is_read: Optional[bool] = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    box_key: Optional[str] = StringField("Box Key")
    box_name: Optional[str] = StringField("Box Name")
    box_type_enum: Optional[BoxTypeEnum] = EnumField("Box Type", enum=BoxTypeEnum)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    message_count: Optional[int] = IntegerField("Message Count")
    root_type: str = StringField("Root Type")
    direction: Optional[DirectionTypeEnum] = EnumField(
        "Direction", enum=DirectionTypeEnum
    )


@resource("message-trashed")
class MessageTrashedQuery(DomainQueryResource):
    """Query resource for message trashed."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "box_key": "trashed",
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_box"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: Optional[bool] = BooleanField("Is Expirable")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: Optional[MessageCategoryEnum] = EnumField(
        "Category", enum=MessageCategoryEnum
    )
    is_read: Optional[bool] = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    box_key: Optional[str] = StringField("Box Key")
    box_name: Optional[str] = StringField("Box Name")
    box_type_enum: Optional[BoxTypeEnum] = EnumField("Box Type", enum=BoxTypeEnum)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    message_count: Optional[int] = IntegerField("Message Count")
    root_type: str = StringField("Root Type")
    direction: Optional[DirectionTypeEnum] = EnumField(
        "Direction", enum=DirectionTypeEnum
    )


@resource("message-thread")
class MessageThreadQuery(DomainQueryResource):
    """Query resource for message thread."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "message_type": MessageTypeEnum.USER.value,
            "thread_id": scope["thread_id"],
            "visible_profile_ids.ov": [profile_id],
        }

    class Meta:
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        scope_required = scope.ThreadIdScope
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_thread"

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    rendered_content: Optional[str] = StringField("Rendered Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    is_important: Optional[bool] = BooleanField("Is Important")
    expirable: Optional[bool] = BooleanField("Is Expirable")
    expiration_date: Optional[str] = DatetimeField("Expiration Date")
    request_read_receipt: Optional[bool] = BooleanField("Request Read Receipt")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    delivery_status: Optional[str] = StringField("Delivery Status")
    data: Optional[dict] = JSONField("Data")
    context: Optional[dict] = JSONField("Context")
    template_key: Optional[str] = StringField("Template Key")
    template_version: Optional[int] = IntegerField("Template Version")
    template_locale: Optional[str] = StringField("Template Locale")
    template_engine: Optional[str] = StringField("Template Engine")
    template_data: Optional[dict] = JSONField("Template Data")
    render_strategy: Optional[str] = StringField("Render Strategy")
    render_status: Optional[str] = StringField("Render Status")
    rendered_at: Optional[str] = DatetimeField("Rendered At")
    render_error: Optional[str] = StringField("Render Error")
    message_count: Optional[int] = IntegerField("Message Count")
    visible_profile_ids: List[UUID_TYPE] = ArrayField("Visible Profile IDs", default=[])
