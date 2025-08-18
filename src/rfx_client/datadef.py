from typing import Optional

from pydantic import Field
from datetime import datetime
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, Availability, SyncStatus, ContactMethod


# Project related payloads


class CreateProjectEstimatorPayload(DataModel):
    """Payload for creating project estimator"""
    name: Optional[str] = Field(max_length=255, default="")
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[Priority] = None


class CreateProjectPayload(DataModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[Priority] = None
    start_date: Optional[datetime] = None
    duration: Optional[str] = None
    lead_id: Optional[UUID_TYPE] = None


class UpdateProjectPayload(DataModel):
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    lead_id: Optional[UUID_TYPE] = None
    duration: Optional[str] = None

# Project BDM Contact related payloads


class CreateProjectBDMContactPayload(DataModel):
    contact_method: Optional[list[ContactMethod]] = None
    message: Optional[str] = None
    meeting_time: Optional[datetime] = None
    status: Optional[str] = None


class UpdateProjectBDMContactPayload(DataModel):
    bdm_contact_id: UUID_TYPE
    contact_method: Optional[list[ContactMethod]] = None
    message: Optional[str] = None
    meeting_time: Optional[datetime] = None
    status: Optional[str] = None


class DeleteProjectBDMContactPayload(DataModel):
    bdm_contact_id: UUID_TYPE


class CreatePromotionPayload(DataModel):
    code: str
    valid_from: datetime
    valid_until: datetime
    max_uses: int
    discount_value: float


class UpdatePromotionPayload(DataModel):
    code: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_uses: Optional[int] = None
    discount_value: Optional[float] = None


class ApplyPromotionPayload(DataModel):
    promotion_code: str


class AddTicketToProjectPayload(DataModel):
    ticket_id: UUID_TYPE


class CreateProjectTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str  # Changed from 'type' to avoid reserved keyword conflict
    priority: Optional[Priority] = Priority.MEDIUM
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    availability: str = "OPEN"
    status: Optional[str] = "DRAFT"
    sync_status: Optional[SyncStatus] = SyncStatus.PENDING


class AddWorkPackageToProjectPayload(DataModel):
    work_package_id: UUID_TYPE


class RemoveWorkPackageFromProjectPayload(DataModel):
    work_package_id: UUID_TYPE


# Work Item related payloads


class CreateWorkItemPayload(DataModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    price_unit: float = Field(gt=0)
    credit_per_unit: float = Field(gt=0)
    estimate: Optional[str] = None


class UpdateWorkItemPayload(DataModel):
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    price_unit: Optional[float] = Field(gt=0)
    credit_per_unit: Optional[float] = Field(gt=0)
    estimate: Optional[str] = None


class CreateWorkItemDeliverablePayload(DataModel):
    """Payload for creating work item deliverable"""
    work_item_id: UUID_TYPE
    name: str = Field(max_length=255)
    description: Optional[str] = None


class UpdateWorkItemDeliverablePayload(DataModel):
    work_item_deliverable_id: UUID_TYPE
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None


class DeleteWorkItemDeliverablePayload(DataModel):
    work_item_deliverable_id: UUID_TYPE


# Work Item Type related payloads

class CreateWorkItemTypePayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    alias: Optional[str] = Field(max_length=50)


class UpdateWorkItemTypePayload(DataModel):
    work_item_type_id: UUID_TYPE
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    alias: Optional[str] = Field(max_length=50)


class DeleteWorkItemTypePayload(DataModel):
    work_item_type_id: UUID_TYPE

# Work Item to Work Package related payloads


class AddWorkItemToWorkPackagePayload(DataModel):
    work_item_id: UUID_TYPE


class RemoveWorkItemFromWorkPackagePayload(DataModel):
    work_item_id: UUID_TYPE


# Project Member related payloads

class AddProjectMemberPayload(DataModel):
    member_id: UUID_TYPE
    role: str


class UpdateProjectMemberRolePayload(DataModel):
    member_id: UUID_TYPE
    role: str


class RemoveProjectMemberPayload(DataModel):
    member_id: UUID_TYPE


# Project Milestone related payloads

class CreateProjectMilestonePayload(DataModel):
    name: str = Field(max_length=255)
    due_date: datetime
    description: Optional[str] = None
    is_completed: Optional[bool] = False


class UpdateProjectMilestonePayload(DataModel):
    milestone_id: UUID_TYPE
    name: Optional[str] = Field(max_length=255)
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = False


class DeleteProjectMilestonePayload(DataModel):
    milestone_id: UUID_TYPE


class UploadProjectResourcePayload(DataModel):
    file: bytes
    type: Optional[str] = None
    description: Optional[str] = None


class DeleteProjectResourcePayload(DataModel):
    resource_id: UUID_TYPE


class CreateProjectCategoryPayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    is_active: bool = True


class UpdateProjectCategoryPayload(DataModel):
    project_category_id: UUID_TYPE
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DeleteProjectCategoryPayload(DataModel):
    project_category_id: UUID_TYPE


# Work Package related payloads


class CreateWorkPackagePayload(DataModel):
    work_package_name: str = Field(max_length=255)
    description: Optional[str] = None
    example_description: Optional[str] = None
    is_custom: bool = False
    complexity_level: Optional[int] = None


class UpdateWorkPackagePayload(DataModel):
    work_package_name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    example_description: Optional[str] = None
    is_custom: Optional[bool] = None

# Project Work Item related payloads


class UpdateProjectWorkItemPayload(DataModel):
    project_work_item_id: UUID_TYPE
    type: Optional[str] = None
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    price_unit: Optional[float] = Field(default=None, gt=0)
    credit_per_unit: Optional[float] = Field(default=None, gt=0)
    estimate: Optional[str] = None


class RemoveProjectWorkItemPayload(DataModel):
    project_work_item_id: UUID_TYPE

# Project Work Package related payloads


class UpdateProjectWorkPackagePayload(DataModel):
    project_work_package_id: UUID_TYPE
    work_package_name: Optional[str] = Field(max_length=255)
    work_package_description: Optional[str] = None
    work_package_example_description: Optional[str] = None
    work_package_is_custom: Optional[bool] = None
    work_package_complexity_level: Optional[int] = None

#  Project Work Item Deliverable related payloads


class UpdateProjectWorkItemDeliverablePayload(DataModel):
    project_work_item_deliverable_id: UUID_TYPE
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None


class DeleteProjectWorkItemDeliverablePayload(DataModel):
    project_work_item_deliverable_id: UUID_TYPE

# Project Work Package Work Item related payloads


class AddNewWorkItemToProjectWorkPackagePayload(DataModel):
    project_work_package_id: UUID_TYPE
    work_item_id: UUID_TYPE


class RemoveProjectWorkItemFromProjectWorkPackagePayload(DataModel):
    project_work_package_id: UUID_TYPE
    project_work_item_id: UUID_TYPE
