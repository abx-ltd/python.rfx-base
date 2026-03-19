from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import UUIDField, StringField, JSONField

from .domain import RFXTodoDomain
from .state import RFXTodoStateManager
from . import scope
from .types import TodoStatusEnum


class RFXTodoQueryManager(DomainQueryManager):
    __data_manager__ = RFXTodoStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXTodoDomain.Meta.namespace
        tags = RFXTodoDomain.Meta.tags


resource = RFXTodoQueryManager.register_resource
endpoint = RFXTodoQueryManager.register_endpoint


@resource("todo")
class TodoQuery(DomainQueryResource):
    """Todo queries."""

    @classmethod
    def base_query(cls, context, scope):
        return {"profile_id": scope["profile_id"]}

    class Meta(DomainQueryResource.Meta):
        resource = "todo"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "todo"
        scope_required = scope.TodoScopeSchema

    resource: str = StringField("Resource")
    resource_id: UUID_TYPE = UUIDField("Resource ID")
    title: str = StringField("Title")
    description: str = StringField("Description")
    status: TodoStatusEnum = StringField("Status")
    profile_id: UUID_TYPE = UUIDField("Profile ID")
    data_payload: dict = JSONField("Data Payload")
