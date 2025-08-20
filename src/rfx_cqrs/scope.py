from pydantic import BaseModel
from fluvius.query.field import UUIDField, StringField
from fluvius.data import UUID_TYPE


class ActivityScopeSchema(BaseModel):
    identifier: UUID_TYPE = UUIDField("Identifier")
    resource: str = StringField("Resource")
