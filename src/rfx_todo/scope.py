from typing import Optional

from fluvius.data import UUID_TYPE
from pydantic import BaseModel


class TodoScopeSchema(BaseModel):
    profile_id: Optional[UUID_TYPE] = None


class TodoItemScopeSchema(BaseModel):
    todo_id: Optional[UUID_TYPE] = None
