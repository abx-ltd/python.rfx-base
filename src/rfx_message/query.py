from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField, UUIDField, BooleanField, DatetimeField, PrimaryID, EnumField, ArrayField
)
from typing import Optional, List

from .state import MessageStateManager
from .domain import MessageServiceDomain
from .types import PriorityLevel, ContentType, MessageType

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

@resource('message')
class MessageQuery(DomainQueryResource):
    """ Query resource for messages. """

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "message"

        # policy_required = True
        scope_optional = ResourceScope

        default_order = ("_created.desc",)
    
    id: UUID_TYPE = PrimaryID("Message ID", weight=100)

    subject: str = StringField("Subject", sortable=True)
    content: str = StringField("Content", sortable=False)
    content_type:  ContentType = EnumField("Content Type", enum=ContentType)

    sender_id: Optional[UUID_TYPE] = UUIDField("Sender ID", ftype="user")

    tags: Optional[List[str]] = ArrayField("Tags", default=[])
    is_important: bool = BooleanField("Is Important")
    expirable: bool = BooleanField("Is Expirable")

    priority: PriorityLevel = EnumField("Priority Level", enum=PriorityLevel)
    message_type: Optional[MessageType] = EnumField("Message Type", enum=MessageType)