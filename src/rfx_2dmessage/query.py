from sqlalchemy import UUID, or_

from .policy import RFX2DMessagePolicyManager
from .domain import RFX2DMessageDomain
from .state import RFX2DMessageStateManager
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

# @resource("mailbox-message")
# class MailboxMessageQuery(DomainQueryResource):
#     class Meta(DomainQueryResource.Meta):
#         include_all = False
#         allow_meta_view = True
#         allow_item_view = True
#         allow_list_view = True

#         excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

#         backend_model = "mailbox_message"

#     mailbox_id: str = UUIDField("mailbox_id")
#     source: Optional[str] = StringField("source")
#     source_id: Optional[str] = StringField("source_id")
#     category_id: Optional[str] = UUIDField("category_id")
#     direction: Optional[str] = StringField("direction")
#     status: Optional[str] = StringField("status")
#     subject: Optional[str] = StringField("subject")
#     body: Optional[str] = StringField("body")
#     profile_id: str = UUIDField("profile_id")
#     sender_profile: Optional[Dict[str, Any]] = JSONField("sender_profile")

@resource("mailbox")
class MailboxListQuery(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

        backend_model = "_mailbox"

    mailbox_name: str = StringField("name")
    mailbox_profile_id: str = UUIDField("profile id")
    telecom_phone: Optional[str] = StringField("telecom_phone")
    telecom_email: Optional[str] = StringField("telecom_email")
    description: Optional[str] = StringField("description")
    url: Optional[str] = StringField("url")
    mailbox_type: Optional[str] = StringField("mailbox_type")
    member_ids: Optional[List[str]] = ArrayField("member_ids", default=[])

    # 🔥 Inject auth filter
    def before_query(self, stmt, **kwargs):
        profile_id = self.context.profile_id  # from auth

        if not profile_id:
            raise ValueError("Missing profile_id in context")
        
        if isinstance(profile_id, str):
            profile_id = UUID(profile_id)
            
        stmt = stmt.where(
            or_(
                # 🔥 member of mailbox
                self.model.member_ids.any(profile_id),

                # 🔥 owner of mailbox (IMPORTANT)
                self.model.mailbox_profile_id == profile_id
            )
        )

        return stmt

@resource("message-mailbox")
class MessageMailboxQuery(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        backend_model = "_message_mailbox_state"
        default_order = ("mailbox_state_updated_at.desc",)

    mailbox_message_id: UUID_TYPE = UUIDField("Mailbox Message ID")
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")
    mailbox_name: Optional[str] = StringField("Mailbox Name")
    message_id: UUID_TYPE = UUIDField("Message ID")
    assigned_to_profile_id: Optional[UUID_TYPE] = UUIDField("Assigned Profile ID")
    folder: Optional[str] = StringField("Folder")
    read: Optional[bool] = BooleanField("Read")
    read_at: Optional[str] = DatetimeField("Read At")
    status: Optional[str] = StringField("Status")
    is_starred: Optional[bool] = BooleanField("Starred")
    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")
    recipient_ids: Optional[List[UUID_TYPE]] = ArrayField("Recipient IDs", default=[])
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    rendered_content: Optional[str] = StringField("Rendered Content")
    content_type: Optional[str] = StringField("Content Type")
    priority: Optional[str] = StringField("Priority")
    message_type: Optional[str] = StringField("Message Type")
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
    expirable: Optional[bool] = BooleanField("Expirable")
    expiration_date: Optional[str] = DatetimeField("Expiration Date")
    request_read_receipt: Optional[str] = DatetimeField("Request Read Receipt")
    category_id: Optional[UUID_TYPE] = UUIDField("Category ID")
    category_name: Optional[str] = StringField("Category Name")
    category_key: Optional[str] = StringField("Category Key")
    tags: Optional[dict] = JSONField("Tags")
    tag_keys: Optional[List[str]] = ArrayField("Tag Keys", default=[])
    attachments: Optional[dict] = JSONField("Attachments")
    actions: Optional[dict] = JSONField("Actions")
