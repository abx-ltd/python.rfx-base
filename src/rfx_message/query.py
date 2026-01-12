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
)


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
            "recipient_id": profile_id,
            "archived": False,
            "trashed": False,
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_inbox"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    from_: UUID_TYPE = UUIDField("From")
    recipient_id: UUID_TYPE = UUIDField("Recipient ID")
    subject: str = StringField("Subject")
    content: str = StringField("Content")
    rendered_content: str = StringField("Rendered Content")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)
    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: bool = BooleanField("Is Expirable")
    priority: PriorityLevelEnum = EnumField("Priority Level", enum=PriorityLevelEnum)
    category: MessageCategoryEnum = EnumField("Category", enum=MessageCategoryEnum)
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    is_read: bool = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    archived: bool = BooleanField("Is Archived", default=False)
    trashed: bool = BooleanField("Is Trashed", default=False)


@resource("message-outbox")
class MessageOutboxQuery(DomainQueryResource):
    """Query resource for message outbox."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "sender_id": profile_id,
            "archived": False,
            "trashed": False,
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_outbox"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    sender_id: UUID_TYPE = UUIDField("Sender ID")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    subject: str = StringField("Subject")
    content: str = StringField("Content")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: bool = BooleanField("Is Expirable")
    priority: PriorityLevelEnum = EnumField("Priority Level", enum=PriorityLevelEnum)
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: MessageCategoryEnum = EnumField("Category", enum=MessageCategoryEnum)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    archived: bool = BooleanField("Is Archived", default=False)
    trashed: bool = BooleanField("Is Trashed", default=False)


@resource("message-archived")
class MessageArchivedQuery(DomainQueryResource):
    """Query resource for message box."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "archived": True,
            "trashed": False,
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

    sender_id: UUID_TYPE = UUIDField("Sender ID")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    subject: str = StringField("Subject")
    content: str = StringField("Content")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: bool = BooleanField("Is Expirable")
    priority: PriorityLevelEnum = EnumField("Priority Level", enum=PriorityLevelEnum)
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: MessageCategoryEnum = EnumField("Category", enum=MessageCategoryEnum)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    archived: bool = BooleanField("Is Archived", default=False)
    trashed: bool = BooleanField("Is Trashed", default=False)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    box_type: str = StringField("Box Type")


@resource("message-trashed")
class MessageTrashedQuery(DomainQueryResource):
    """Query resource for message trashed."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "trashed": True,
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

    sender_id: UUID_TYPE = UUIDField("Sender ID")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    subject: str = StringField("Subject")
    content: str = StringField("Content")
    content_type: ContentTypeEnum = EnumField("Content Type", enum=ContentTypeEnum)
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: bool = BooleanField("Is Expirable")
    priority: PriorityLevelEnum = EnumField("Priority Level", enum=PriorityLevelEnum)
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: MessageCategoryEnum = EnumField("Category", enum=MessageCategoryEnum)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    archived: bool = BooleanField("Is Archived", default=False)
    trashed: bool = BooleanField("Is Trashed", default=False)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    box_type: str = StringField("Box Type")
