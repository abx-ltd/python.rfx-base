# from .policy import RFX2DMessagePolicyManager
from .domain import RFX2DMessageDomain
from .state import RFX2DMessageStateManager
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField, BooleanField, DateField, UUIDField, PrimaryID, EnumField,
    ArrayField, IntegerField, JSONField, FloatField, DatetimeField, DateField
)
from typing import Optional, Dict, Any
import uuid
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

class RFX2DMessageQueryManager(DomainQueryManager):
    __data_manager__ = RFX2DMessageStateManager
    # __policymgr__ = RFX2DMessagePolicyManager

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
    resource: Optional[str] = StringField("resource")
    url: Optional[str] = StringField("url")
    mailbox_type: Optional[str] = StringField("mailbox_type")

# @resource("all-message-mailbox")
# class AllMessageInMailboxQuery(DomainQueryResource):
#     class Meta(DomainQueryResource.Meta):
#         include_all = False
#         allow_meta_view = True
#         allow_item_view = True
#         allow_list_view = True

#         excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

#         backend_model = "_mailbox"
    
#     mailbox_name: str = StringField("name")


    

@resource("message-sender-detail")
class MessageSenderQuery(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_meta_view = True
        allow_item_view = True
        allow_list_view = True
        # allow_text_search = True

        excluded_fields = ('_creator', '_deleted', '_etag', '_updater')

        backend_model = "_message_sender_detail"


    sender_id: str = UUIDField("sender_id")
    subject: str = StringField("subject")
    content: str = StringField("content")

    send_at: str = DatetimeField("message_created_at")

    message: Optional[Dict[str, Any]] = JSONField("message")

    box_name: str = StringField("box_name")
    is_archived: bool = BooleanField("is_archived")
    is_starred: bool = BooleanField("is_starred")