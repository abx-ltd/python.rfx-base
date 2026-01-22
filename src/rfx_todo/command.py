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
        result = await agg.update_todo(payload)
        yield agg.create_response(serialize_mapping(result), _type="todo-response")


class SetTodoCompleted(Command):
    """Set todo completed status."""

    Data = datadef.SetTodoCompletedPayload

    class Meta:
        key = "set-todo-completed"
        resources = ("todo",)
        tags = ["todo", "complete"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.set_todo_completed(payload.completed)
        yield agg.create_response(serialize_mapping(result), _type="todo-response")


class DeleteTodo(Command):
    """Delete todo (soft delete)."""

    Data = datadef.DeleteTodoPayload

    class Meta:
        key = "delete-todo"
        resources = ("todo",)
        tags = ["todo", "delete"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.delete_todo()
        yield agg.create_response(serialize_mapping(result), _type="todo-response")


class CreateTodoItem(Command):
    """Create a todo item."""

    Data = datadef.CreateTodoItemPayload

    class Meta:
        key = "create-todo-item"
        resources = ("todo_item",)
        tags = ["todo-item", "create"]
        auth_required = True
        policy_required = False
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_todo_item(payload)
        yield agg.create_response(serialize_mapping(result), _type="todo-item-response")


class UpdateTodoItem(Command):
    """Update a todo item."""

    Data = datadef.UpdateTodoItemPayload

    class Meta:
        key = "update-todo-item"
        resources = ("todo_item",)
        tags = ["todo-item", "update"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.update_todo_item(payload)
        yield agg.create_response(serialize_mapping(result), _type="todo-item-response")


class SetTodoItemCompleted(Command):
    """Set todo item completed status."""

    Data = datadef.SetTodoItemCompletedPayload

    class Meta:
        key = "set-todo-item-completed"
        resources = ("todo_item",)
        tags = ["todo-item", "complete"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.set_todo_item_completed(payload.completed)
        yield agg.create_response(serialize_mapping(result), _type="todo-item-response")


class DeleteTodoItem(Command):
    """Delete todo item (soft delete)."""

    Data = datadef.DeleteTodoItemPayload

    class Meta:
        key = "delete-todo-item"
        resources = ("todo_item",)
        tags = ["todo-item", "delete"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.delete_todo_item()
        yield agg.create_response(serialize_mapping(result), _type="todo-item-response")
