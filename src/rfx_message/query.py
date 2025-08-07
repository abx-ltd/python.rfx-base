from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField, BooleanField, DatetimeField, UUIDField, PrimaryID, EnumField, ArrayField
)
from typing import Optional, List

from .state import MessageStateManager
from .domain import MessageServiceDomain
from .types import PriorityLevel, ContentType, MessageType
from . import logger

class MessageQueryManager(DomainQueryManager):
    __data_manager__ = MessageStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = MessageServiceDomain.Meta.prefix
        tags = MessageServiceDomain.Meta.tags

resource = MessageQueryManager.register_resource
endpoint = MessageQueryManager.register_endpoint

class ResourceScope(BaseModel):
    resource: str
    resource_id: str

@resource('_message_recipients')
class MessageQuery(DomainQueryResource):
    """ Query resource for notifications received by the current user. """

    @classmethod
    def base_query(cls, context, scope):
        user_id = context.user._id
        return {"recipient_id": user_id}
        
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_recipients"

        # policy_required = True  # Enable access control
        scope_optional = ResourceScope

        default_order = ("_created.desc",)
    
    # Primary key fields from the view
    record_id: UUID_TYPE = UUIDField("Record ID")
    message_id: UUID_TYPE = UUIDField("Message ID")
    recipient_id: UUID_TYPE = UUIDField("Recipient ID")

    subject: str = StringField("Subject")
    content: str = StringField("Content")
    content_type:  ContentType = EnumField("Content Type", enum=ContentType)

    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID")

    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    expirable: bool = BooleanField("Is Expirable")

    priority: PriorityLevel = EnumField("Priority Level", enum=PriorityLevel)
    message_type: Optional[MessageType] = EnumField("Message Type", enum=MessageType)
    
    # Notification-specific fields for recipients
    is_read: bool = BooleanField("Is Read", default=False)
    read_at: Optional[str] = DatetimeField("Read At")
    archived: bool = BooleanField("Is Archived", default=False)