from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class WorkItemListingScopeSchema(BaseModel):
    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
