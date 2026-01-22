from typing import Optional
from datetime import datetime

from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import UUIDField, StringField, BooleanField, DatetimeField

from .domain import RFXTodoDomain
from .state import RFXTodoStateManager
from . import scope


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
        return {"scope_id": scope["scope_id"]}

    class Meta(DomainQueryResource.Meta):
        resource = "todo"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "todo"
        scope_required = scope.TodoScopeSchema

    title: str = StringField("Title")
    description: str = StringField("Description")
    completed: bool = BooleanField("Completed")
    scope_id: UUID_TYPE = UUIDField("Scope ID")


@resource("todo-item")
class TodoItemQuery(DomainQueryResource):
    """Todo item queries."""

    # @classmethod
    # def base_query(cls, context, scope):

    class Meta(DomainQueryResource.Meta):
        resource = "todo_item"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "todo_item"
        scope_optional = scope.TodoItemScopeSchema

    todo_id: UUID_TYPE = UUIDField("Todo ID")
    type: str = StringField("Type")
    name: str = StringField("Name")
    description: str = StringField("Description")
    completed: bool = BooleanField("Completed")
    due_date: Optional[datetime] = DatetimeField("Due Date")
