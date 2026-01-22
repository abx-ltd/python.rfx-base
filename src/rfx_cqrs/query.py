from .domain import RFXCqrsDomain
from .state import RFXCqrsStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, IntegerField, DictField
from . import scope


class RFXCqrsQueryManager(DomainQueryManager):
    __data_manager__ = RFXCqrsStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXCqrsDomain.Meta.namespace
        tags = RFXCqrsDomain.Meta.tags


resource = RFXCqrsQueryManager.register_resource
endpoint = RFXCqrsQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


@resource("activity")
class ProjectActivityLogQuery(DomainQueryResource):
    """Activity log queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "activity-log"
        scope_required = scope.ActivityScopeSchema

    domain: str = StringField("Domain")
    identifier: UUID_TYPE = UUIDField("Identifier")
    resource: str = StringField("Resource")
    message: str = StringField("Message")
    msgtype: str = StringField("Message Type")
    msglabel: str = StringField("Message Label")
    context: UUID_TYPE = UUIDField("Context")
    src_cmd: UUID_TYPE = UUIDField("Source Command")
    src_evt: UUID_TYPE = UUIDField("Source Event")
    data: dict = DictField("Data")
    code: int = IntegerField("Code")
