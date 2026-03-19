from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE

from .types import TodoStatusEnum


class CreateTodoPayload(DataModel):
    title: str = Field(..., description="Todo title")
    description: str = Field(..., description="Todo description")
    resource: str = Field(..., description="Resource for the todo")
    resource_id: UUID_TYPE = Field(..., description="Resource ID for the todo")
    status: TodoStatusEnum = Field(..., description="Status for the todo")
    profile_id: UUID_TYPE = Field(..., description="Profile ID for the todo")
    data_payload: dict = Field(default={}, description="Data payload for the todo")


class UpdateTodoPayload(DataModel):
    title: Optional[str] = Field(default=None, description="Todo title")
    description: Optional[str] = Field(default=None, description="Todo description")
    resource: Optional[str] = Field(default=None, description="Resource for the todo")
    resource_id: Optional[UUID_TYPE] = Field(
        default=None, description="Resource ID for the todo"
    )
    status: Optional[TodoStatusEnum] = Field(
        default=None, description="Status for the todo"
    )
    profile_id: Optional[UUID_TYPE] = Field(
        default=None, description="Profile ID for the todo"
    )
    data_payload: Optional[dict] = Field(
        default=None, description="Data payload for the todo"
    )
