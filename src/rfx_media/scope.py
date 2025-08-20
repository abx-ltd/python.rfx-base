from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class ResourceScope(BaseModel):
    resource: str
    resource__id: str
