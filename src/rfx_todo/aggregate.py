from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR


class RFXTodoAggregate(Aggregate):
    """Todo Aggregate - CRUD operations for todo items."""

    @action("todo-created", resources="todo")
    async def create_todo(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "todo",
            data,
            id=UUID_GENR(),
            completed=False if data.get("completed") is None else data.get("completed"),
        )
        await self.statemgr.insert(record)
        return record

    @action("todo-updated", resources="todo")
    async def update_todo(self, /, data):
        data = {k: v for k, v in serialize_mapping(data).items() if v is not None}
        await self.statemgr.update(self.rootobj, **data)
        return self.rootobj

    @action("todo-completed-set", resources="todo")
    async def set_todo_completed(self, /, completed: bool):
        await self.statemgr.update(self.rootobj, completed=completed)
        return self.rootobj

    @action("todo-deleted", resources="todo")
    async def delete_todo(self, /):
        await self.statemgr.invalidate(self.rootobj)
        return {"status": "deleted"}

    @action("todo-item-created", resources="todo_item")
    async def create_todo_item(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "todo_item",
            data,
            id=UUID_GENR(),
            completed=False if data.get("completed") is None else data.get("completed"),
        )
        await self.statemgr.insert(record)
        return record

    @action("todo-item-updated", resources="todo_item")
    async def update_todo_item(self, /, data):
        data = {k: v for k, v in serialize_mapping(data).items() if v is not None}
        await self.statemgr.update(self.rootobj, **data)
        return self.rootobj

    @action("todo-item-completed-set", resources="todo_item")
    async def set_todo_item_completed(self, /, completed: bool):
        await self.statemgr.update(self.rootobj, completed=completed)
        return self.rootobj

    @action("todo-item-deleted", resources="todo_item")
    async def delete_todo_item(self, /):
        await self.statemgr.invalidate(self.rootobj)
        return {"status": "deleted"}
