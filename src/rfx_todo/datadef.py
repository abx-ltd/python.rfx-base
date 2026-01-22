from typing import Optional
from datetime import datetime

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE


class CreateTodoPayload(DataModel):
    title: str = Field(..., description="Todo title")
    description: str = Field(..., description="Todo description")
    scope_id: UUID_TYPE = Field(..., description="Scope ID for the todo")
    completed: Optional[bool] = Field(default=False, description="Completed status")


class UpdateTodoPayload(DataModel):
    title: Optional[str] = Field(default=None, description="Todo title")
    description: Optional[str] = Field(default=None, description="Todo description")
    scope_id: Optional[UUID_TYPE] = Field(
        default=None, description="Scope ID for the todo"
    )
    completed: Optional[bool] = Field(default=None, description="Completed status")


class CreateTodoItemPayload(DataModel):
    type: str = Field(..., description="Todo item type")
    name: str = Field(..., description="Todo item name")
    description: str = Field(..., description="Todo item description")
    completed: Optional[bool] = Field(default=False, description="Completed status")
    due_date: Optional[datetime] = Field(default=None, description="Due date")


class UpdateTodoItemPayload(DataModel):
    item_id: UUID_TYPE = Field(..., description="Todo item ID")
    type: Optional[str] = Field(default=None, description="Todo item type")
    name: Optional[str] = Field(default=None, description="Todo item name")
    description: Optional[str] = Field(
        default=None, description="Todo item description"
    )
    completed: Optional[bool] = Field(default=None, description="Completed status")
    due_date: Optional[datetime] = Field(default=None, description="Due date")


class RemoveTodoItemPayload(DataModel):
    item_id: UUID_TYPE = Field(..., description="Todo item ID")
