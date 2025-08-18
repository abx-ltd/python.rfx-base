from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class ActivityIdentifierScopeSchema(BaseModel):
    identifier: UUID_TYPE = UUIDField("Identifier")
