from fluvius.data import serialize_mapping

from .domain import RFXTodoDomain
from . import datadef

processor = RFXTodoDomain.command_processor
Command = RFXTodoDomain.Command


class CreateTodo(Command):
    """Create a todo item."""

    Data = datadef.CreateTodoPayload

    class Meta:
        key = "create-todo"
        resources = ("todo",)
        tags = ["todo", "create"]
        auth_required = True
        policy_required = False
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_todo(payload)
        yield agg.create_response(serialize_mapping(result), _type="todo-response")


class UpdateTodo(Command):
    """Update a todo item."""

    Data = datadef.UpdateTodoPayload

    class Meta:
        key = "update-todo"
        resources = ("todo",)
        tags = ["todo", "update"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.update_todo(data=payload)


class RemoveTodo(Command):
    """Remove todo (soft delete)."""

    class Meta:
        key = "remove-todo"
        resources = ("todo",)
        tags = ["todo", "remove"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.remove_todo()
