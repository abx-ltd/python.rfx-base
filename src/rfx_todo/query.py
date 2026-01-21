from typing import Optional

from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import UUIDField, StringField, BooleanField

from .domain import RFXTodoDomain
from .state import RFXTodoStateManager
from . import scope


class RFXTodoQueryManager(DomainQueryManager):
    __data_manager__ = RFXTodoStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXTodoDomain.Meta.prefix
        tags = RFXTodoDomain.Meta.tags


resource = RFXTodoQueryManager.register_resource
endpoint = RFXTodoQueryManager.register_endpoint


@resource("todo")
class TodoQuery(DomainQueryResource):
    """Todo queries."""

    @classmethod
    def base_query(cls, context, scope):
        where = {}
        if scope.get("assignee_id") is not None:
            where["assignee_id"] = scope["assignee_id"]
        if scope.get("completed") is not None:
            where["completed.eq"] = scope["completed"]
        return where

    class Meta(DomainQueryResource.Meta):
        resource = "todo"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "todo"
        scope_optional = scope.TodoScopeSchema

    id: UUID_TYPE = UUIDField("Todo ID", filterable=True)
    title: str = StringField("Title", filterable=True)
    description: str = StringField("Description")
    completed: bool = BooleanField("Completed", filterable=True)
    assignee_id: Optional[UUID_TYPE] = UUIDField("Assignee ID", filterable=True)


