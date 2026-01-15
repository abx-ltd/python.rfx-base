from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class ThreadIdScope(BaseModel):
    thread_id: UUID_TYPE = UUIDField("Thread ID")
