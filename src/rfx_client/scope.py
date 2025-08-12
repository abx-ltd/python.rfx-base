from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class WorkItemListingScopeSchema(BaseModel):
    work_package_id: UUID_TYPE = UUIDField("Work Package ID")


class ProjectBDMContactScopeSchema(BaseModel):
    project_id: UUID_TYPE = UUIDField("Project ID")


class ProjectMilestoneScopeSchema(BaseModel):
    project_id: UUID_TYPE = UUIDField("Project ID")


class ProjectWorkPackageScopeSchema(BaseModel):
    project_id: UUID_TYPE = UUIDField("Project ID")
