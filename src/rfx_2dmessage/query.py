from sqlalchemy import UUID, or_

from .policy import RFX2DMessagePolicyManager
from .domain import RFX2DMessageDomain
from .state import RFX2DMessageStateManager
from . import scope
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField, BooleanField, DateField, UUIDField, PrimaryID, EnumField,
    ArrayField, IntegerField, JSONField, FloatField, DatetimeField, DateField
)

from typing import Optional, List, Dict, Any
from . import scope

class RFX2DMessageQueryManager(DomainQueryManager):
    __data_manager__ = RFX2DMessageStateManager
    __policymgr__ = RFX2DMessagePolicyManager

    class Meta(DomainQueryResource.Meta):
        prefix = RFX2DMessageDomain.Meta.namespace
        tags = RFX2DMessageDomain.Meta.tags

resource = RFX2DMessageQueryManager.register_resource
endpoint = RFX2DMessageQueryManager.register_endpoint

@resource("mailbox")
class MailboxListQuery(DomainQueryResource):
    """Query for listing mailboxes that the user has joined or hosts."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "member_id": profile_id,
        }
    
    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

        backend_model = "_mailbox"

    # Mailbox identity fields
    mailbox_id: Optional[UUID_TYPE] = UUIDField("Mailbox ID")
    mailbox_name: Optional[str] = StringField("name")
    mailbox_profile_id: Optional[UUID_TYPE] = UUIDField("host profile id")
    
    # Contact fields
    telecom_phone: Optional[str] = StringField("telecom_phone")
    telecom_email: Optional[str] = StringField("telecom_email")
    description: Optional[str] = StringField("description")
    url: Optional[str] = StringField("url")
    mailbox_type: Optional[str] = StringField("mailbox_type")  

    member_id: UUID_TYPE = UUIDField("member_id")
    members: List[UUID_TYPE] = ArrayField("member_list", default=[])
    tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    categories: Optional[List[Dict[str, Any]]] = JSONField("categories")

@resource("mailbox-message")
class MailboxMessageQuery(DomainQueryResource):
    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "mailbox_id": scope["mailbox_id"],
            "assigned_to_profile_id": profile_id,
        }
    
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_meta_view = True
        allow_item_view = False
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

        backend_model = "_message_mailbox" 

    mailbox_id: str = UUIDField("mailbox_id")

    assigned_to_profile_id: Optional[str] = UUIDField("assigned_to_profile_id") 

    status: Optional[str] = StringField("status")
    subject: Optional[str] = StringField("subject")

    content: Optional[str] = StringField("content")

    is_starred: Optional[bool] = BooleanField("is_starred")
    tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    category_id: Optional[str] = UUIDField("category_id")

@resource("message-detail")
class MessageQuery(DomainQueryResource):
    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "mailbox_id": scope["mailbox_id"],
            "assigned_to_profile_id": profile_id,
        }
    
    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        backend_model = "_message_mailbox_state"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    mailbox_message_id: UUID_TYPE = UUIDField("Mailbox Message ID")
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")
    message_id: UUID_TYPE = UUIDField("Message ID")
    assigned_to_profile_id: Optional[UUID_TYPE] = UUIDField("Assigned Profile ID")
    folder: Optional[str] = StringField("Folder")
    status: Optional[str] = StringField("Status")
    is_starred: Optional[bool] = BooleanField("Starred")
    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    rendered_content: Optional[str] = StringField("Rendered Content")
    content_type: Optional[str] = StringField("Content Type")
    priority: Optional[str] = StringField("Priority")
    message_type: Optional[str] = StringField("Message Type")
    expirable: Optional[bool] = BooleanField("Expirable")
    expiration_date: Optional[str] = DatetimeField("Expiration Date")
    category_id: Optional[UUID_TYPE] = UUIDField("Category ID")
    category_name: Optional[str] = StringField("Category Name")
    category_key: Optional[str] = StringField("Category Key")
    # tags: Optional[dict] = JSONField("Tags")
    # tag_keys: Optional[List[str]] = ArrayField("Tag Keys", default=[])
    attachments: Optional[dict] = JSONField("Attachments")
    actions: Optional[dict] = JSONField("Actions")

    
# @resource("message-mailbox")
# class MessageMailboxQuery(DomainQueryResource):
#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_meta_view = True
#         allow_item_view = True
#         allow_list_view = True
#         auth_required = True

#         backend_model = "_message_mailbox_state"

#         excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

#     mailbox_message_id: UUID_TYPE = UUIDField("Mailbox Message ID")
#     mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")
#     mailbox_name: Optional[str] = StringField("Mailbox Name")
#     message_id: UUID_TYPE = UUIDField("Message ID")
#     assigned_to_profile_id: Optional[UUID_TYPE] = UUIDField("Assigned Profile ID")
#     folder: Optional[str] = StringField("Folder")
#     read: Optional[bool] = BooleanField("Read")
#     read_at: Optional[str] = DatetimeField("Read At")
#     status: Optional[str] = StringField("Status")
#     is_starred: Optional[bool] = BooleanField("Starred")
#     sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")
#     recipient_ids: Optional[List[UUID_TYPE]] = ArrayField("Recipient IDs", default=[])
#     subject: Optional[str] = StringField("Subject")
#     content: Optional[str] = StringField("Content")
#     rendered_content: Optional[str] = StringField("Rendered Content")
#     content_type: Optional[str] = StringField("Content Type")
#     priority: Optional[str] = StringField("Priority")
#     message_type: Optional[str] = StringField("Message Type")
#     expirable: Optional[bool] = BooleanField("Expirable")
#     expiration_date: Optional[str] = DatetimeField("Expiration Date")
#     request_read_receipt: Optional[str] = DatetimeField("Request Read Receipt")
#     category_id: Optional[UUID_TYPE] = UUIDField("Category ID")
#     category_name: Optional[str] = StringField("Category Name")
#     category_key: Optional[str] = StringField("Category Key")
#     tags: Optional[dict] = JSONField("Tags")
#     tag_keys: Optional[List[str]] = ArrayField("Tag Keys", default=[])
#     attachments: Optional[dict] = JSONField("Attachments")
#     actions: Optional[dict] = JSONField("Actions")

@resource("tag")
class TagQuery(DomainQueryResource):
    
    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "profile_id": profile_id,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True
        
        resource = "tag"
        backend_model = "tag"
        default_order = ("_created",)

    key: str = StringField("Tag Key")
    name: str = StringField("Tag name")
    background_color: Optional[str] = StringField("Background color of tag")
    font_color: Optional[str] = StringField("Font color of tag")
    description: Optional[str] = StringField("Description of tag")

@resource("message-tag")
class MessageTagQuery(DomainQueryResource):
    @classmethod
    def base_query(cls, context, scope):
        # profile_id = context.profile._id
        return {
            "mailbox_id": scope["mailbox_id"],
            # "assigned_to_profile_id": profile_id,
        }
    
    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        backend_model = "_message_mailbox_state"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    mailbox_id: str = UUIDField("mailbox_id")

    tag_id: Optional[str] = UUIDField("tag_id")
    tag_key: Optional[str] = StringField("tag_key")

    category_id: Optional[str] = UUIDField("category_id")

    search: Optional[str] = StringField("search")
    
# @resource("get-embedded-action-callback")
# class GetEmbeddedActionCallback(DomainQueryResource):
#     """Get callback configuration for an embedded action execution."""

#     class Meta(DomainQueryResource.Meta):
#         include_all = False
#         allow_meta_view = False
#         allow_item_view = False
#         allow_list_view = False
#         allow_custom_view = True

#     execution_id: str = StringField("Execution ID", required=True)

#     async def get_custom_view(self, **kwargs):
#         """Return callback config for the given execution_id."""
#         execution_id = kwargs.get("execution_id")
#         if not execution_id:
#             raise ValueError("execution_id is required")

#         # Get the execution record
#         execution = await self.statemgr.find_one(
#             "message_action_execute",
#             where={"_id": execution_id, "_deleted": None}
#         )
#         if not execution:
#             raise ValueError("Action execution not found")

#         # Get the action definition
#         action = await self.statemgr.find_one(
#             "message_action",
#             where={"_id": execution.action_id, "_deleted": None}
#         )
#         if not action:
#             raise ValueError("Action definition not found")

#         # Return callback config
#         callback_config = action.embedded_json.get("callback_method", {}) if action.embedded_json else {}
#         return {
#             "execution_id": str(execution_id),
#             "callback": callback_config
#         }
