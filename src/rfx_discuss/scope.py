from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class CommentScopeSchema(BaseModel):
    resource_id: UUID_TYPE = UUIDField("Resource ID")
