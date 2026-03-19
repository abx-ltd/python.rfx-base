from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.domain.aggregate import Aggregate, action

class RFXTodoAggregate(Aggregate):
    """Todo Aggregate - CRUD operations for todo items."""

    @action("todo-created", resources="todo")
    async def create_todo(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "todo",
            data,
            _id=UUID_GENR(),
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

    @action("todo-removed", resources="todo")
    async def remove_todo(self, /):
        await self.statemgr.invalidate(self.rootobj)

    @action("todo-item-created", resources="todo")
    async def create_todo_item(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "todo_item",
            data,
            _id=UUID_GENR(),
            todo_id=self.rootobj._id,
        )
        await self.statemgr.insert(record)
        return record

    @action("todo-item-updated", resources="todo")
    async def update_todo_item(self, /, data):
        todo = self.rootobj
        todo_item = await self.statemgr.find_one(
            "todo_item", where=dict(todo_id=todo._id, _id=data.item_id)
        )
        data = serialize_mapping(data)
        data.pop("item_id")
        await self.statemgr.update(todo_item, **data)

    @action("todo-item-removed", resources="todo")
    async def remove_todo_item(self, /, data):
        todo = self.rootobj
        todo_item = await self.statemgr.find_one(
            "todo_item", where=dict(todo_id=todo._id, _id=data.item_id)
        )
        await self.statemgr.invalidate(todo_item)
