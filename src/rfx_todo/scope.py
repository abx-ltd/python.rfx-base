from typing import Optional

from fluvius.data import UUID_TYPE
from pydantic import BaseModel


class TodoScopeSchema(BaseModel):
    assignee_id: Optional[UUID_TYPE] = None
    completed: Optional[bool] = None


