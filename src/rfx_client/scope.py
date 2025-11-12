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


class WorkItemDeliverableScopeSchema(BaseModel):
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")


class ProjectWorkItemListingScopeSchema(BaseModel):
    project_work_package_id: UUID_TYPE = UUIDField("Project Work Package ID")


## Ticket Scopes
class TicketScopeSchema(BaseModel):
    project_id: UUID_TYPE = UUIDField("Project ID")


class CommentScopeSchema(BaseModel):
    resource_id: UUID_TYPE = UUIDField("Resource ID")


class CommentAttachmentScopeSchema(BaseModel):
    comment_id: UUID_TYPE = UUIDField("Comment ID")


class CommentReactionScopeSchema(BaseModel):
    comment_id: UUID_TYPE = UUIDField("Comment ID")


class OrganizationScopeSchema(BaseModel):
    organization_id: UUID_TYPE = UUIDField("Organization ID")
