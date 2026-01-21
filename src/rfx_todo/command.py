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


class AssignTodo(Command):
    """Assign todo to a user/profile."""

    Data = datadef.AssignTodoPayload

    class Meta:
        key = "assign-todo"
        resources = ("todo",)
        tags = ["todo", "assign"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.assign_todo(payload.assignee_id)
        yield agg.create_response(serialize_mapping(result), _type="todo-response")


class UnassignTodo(Command):
    """Unassign todo."""

    Data = datadef.UnassignTodoPayload

    class Meta:
        key = "unassign-todo"
        resources = ("todo",)
        tags = ["todo", "unassign"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.unassign_todo()
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
