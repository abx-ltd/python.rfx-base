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
from datetime import datetime

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

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater', 'member_id')

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
    # members: Dict = JSONField("members")
    # tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    # categories: Optional[List[Dict[str, Any]]] = JSONField("categories")

@resource("mailbox-folder-count")
class MailboxFolderCount(DomainQueryResource):
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
        backend_model = "_mailbox_folder"

        # excluded_fields = ('assigned_to_profile_id')

    mailbox_id: str = UUIDField("mailbox_id")
    mailbox_name: str = StringField("mailbox_name")

    assigned_to_profile_id: Optional[str] = UUIDField("assigned_to_profile_id")    
    inbox_count: int = IntegerField("Inbox message count")
    trashed_count: int = IntegerField("Trash message count")
    archived_count: int = IntegerField("Archive message count")
    total_count: int = IntegerField("Total message count")
    

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
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

        backend_model = "_message_mailbox" 

    mailbox_id: str = UUIDField("mailbox_id")
    mailbox_name: str = StringField("mailbox_name")

    assigned_to_profile_id: Optional[str] = UUIDField("assigned_to_profile_id") 
    sender_name: Optional[str] = StringField("Sender name")
    sender_email: Optional[str] = StringField("Sender email")
    # message_id: str = UUIDField("message_id")
    folder: str = StringField("folder")
    is_starred: Optional[bool] = BooleanField("is_starred")
    priority: str = StringField("priority")
    status: Optional[str] = StringField("status")
    message_type: str = StringField("message_type")
    is_important: bool = BooleanField("is_important")
    subject: Optional[str] = StringField("subject")
    content: Optional[str] = StringField("content")
    message_created_at: datetime = DatetimeField("message_created_at")
    category_id: str = StringField("category_id")
    category_name: str = StringField("category_name")
    category_key: str = StringField("category_key")
    tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    category_id: Optional[str] = UUIDField("category_id")
    attachments: Optional[List[Dict[str, Any]]] = JSONField("attachments")

@resource("tag")
class TagQuery(DomainQueryResource):
    @classmethod
    def base_query(cls, context, scope):
        return {
            "mailbox_id": scope["mailbox_id"],
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True
        
        scope_required = scope.MailboxScope
        resource = "tag"
        backend_model = "tag"
        default_order = ("_created",)

    key: str = StringField("Tag Key")
    name: str = StringField("Tag name")
    background_color: Optional[str] = StringField("Background color of tag")
    font_color: Optional[str] = StringField("Font color of tag")
    description: Optional[str] = StringField("Description of tag")
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")

@resource("message-tag")
class MessageTagQuery(DomainQueryResource):
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
        backend_model = "_message_tag"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    mailbox_id: str = UUIDField("mailbox_id")
    mailbox_name: str = StringField("mailbox_name")

    assigned_to_profile_id: Optional[str] = UUIDField("assigned_to_profile_id") 
    sender_name: Optional[str] = StringField("Sender name")
    sender_email: Optional[str] = StringField("Sender email")
    message_id: str = UUIDField("message_id")
    folder: str = StringField("folder")
    is_starred: Optional[bool] = BooleanField("is_starred")
    priority: str = StringField("priority")
    status: Optional[str] = StringField("status")
    message_type: str = StringField("message_type")
    is_important: bool = BooleanField("is_important")
    subject: Optional[str] = StringField("subject")
    content: Optional[str] = StringField("content")
    message_created_at: datetime = DatetimeField("message_created_at")
    category_id: str = StringField("category_id")
    category_name: str = StringField("category_name")
    category_key: str = StringField("category_key")
    # tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    category_id: Optional[str] = UUIDField("category_id")
    attachments: Optional[List[Dict[str, Any]]] = JSONField("attachments")

@resource("category")
class CategoryQuery(DomainQueryResource):
    @classmethod
    def base_query(cls, context, scope):
        return {
            "mailbox_id": scope["mailbox_id"],
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        backend_model = "category"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    key: str = StringField("Category Key")
    name: str = StringField("Category name")
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")

@resource("message-category")
class MessageCategoryQuery(DomainQueryResource):
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
        allow_item_view = True
        allow_list_view = True
        auth_required = True

        scope_required = scope.MailboxScope
        backend_model = "_message_category"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    mailbox_id: str = UUIDField("mailbox_id")
    mailbox_name: str = StringField("mailbox_name")

    assigned_to_profile_id: Optional[str] = UUIDField("assigned_to_profile_id") 
    sender_name: Optional[str] = StringField("Sender name")
    sender_email: Optional[str] = StringField("Sender email")
    message_id: str = UUIDField("message_id")
    folder: str = StringField("folder")
    is_starred: Optional[bool] = BooleanField("is_starred")
    priority: str = StringField("priority")
    status: Optional[str] = StringField("status")
    message_type: str = StringField("message_type")
    is_important: bool = BooleanField("is_important")
    subject: Optional[str] = StringField("subject")
    content: Optional[str] = StringField("content")
    message_created_at: datetime = DatetimeField("message_created_at")
    category_id: str = StringField("category_id")
    category_name: str = StringField("category_name")
    category_key: str = StringField("category_key")
    tags: Optional[List[Dict[str, Any]]] = JSONField("tags")
    category_id: Optional[str] = UUIDField("category_id")
    attachments: Optional[List[Dict[str, Any]]] = JSONField("attachments")

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
        allow_list_view = False
        auth_required = True

        scope_required = scope.MailboxScope
        backend_model = "_message_detail"

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

    mailbox_message_id: UUID_TYPE = UUIDField("Mailbox Message ID")
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")
    message_id: UUID_TYPE = UUIDField("Message ID")
    assigned_to_profile_id: Optional[UUID_TYPE] = UUIDField("Assigned Profile ID")
    sender_name: Optional[str] = StringField("Sender name")
    sender_email: Optional[str] = StringField("Sender email")
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
    tags: Optional[dict] = JSONField("Tags")
    attachments: Optional[dict] = JSONField("Attachments")
    linked_messages: Optional[dict] = JSONField("Linked message")
    actions: Optional[dict] = JSONField("Actions")

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
