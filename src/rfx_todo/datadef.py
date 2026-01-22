from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE


class CreateTodoPayload(DataModel):
    title: str = Field(..., description="Todo title")
    description: str = Field(..., description="Todo description")
    assignee_id: Optional[UUID_TYPE] = Field(default=None, description="Assignee profile id")


class UpdateTodoPayload(DataModel):
    title: Optional[str] = Field(default=None, description="Todo title")
    description: Optional[str] = Field(default=None, description="Todo description")
    assignee_id: Optional[UUID_TYPE] = Field(default=None, description="Assignee profile id")
    completed: Optional[bool] = Field(default=None, description="Completed status")


class SetTodoCompletedPayload(DataModel):
    completed: bool = Field(..., description="Completed status")


class AssignTodoPayload(DataModel):
    assignee_id: UUID_TYPE = Field(..., description="Assignee profile id")


class UnassignTodoPayload(DataModel):
    pass


class DeleteTodoPayload(DataModel):
    pass
