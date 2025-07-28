from typing import Optional, List
from uuid import UUID
from pydantic import Field
from datetime import datetime
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, ProjectStatus, Availability, SyncStatus

# Project related payloads


class CreateProjectEstimatorPayload(DataModel):
    """Payload for creating project estimator"""
    name: Optional[str] = Field(max_length=255, default="")
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Priority = Priority.MEDIUM


class CreateProjectPayload(DataModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    lead_id: Optional[UUID_TYPE] = None


class ConvertEstimatorToProjectPayload(DataModel):
    """Payload for converting estimator to project"""
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[Priority] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
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
    external_project_id: Optional[str] = None
    external_provider: Optional[str] = None


class AddWorkPackageToProjectPayload(DataModel):
    work_package_id: UUID_TYPE
    quantity: int = Field(ge=1)


class UpdateWorkPackageQuantityPayload(DataModel):
    work_package_id: UUID_TYPE
    quantity: int = Field(ge=1)


class RemoveWorkPackagePayload(DataModel):
    work_package_id: UUID_TYPE


class ApplyReferralCodePayload(DataModel):
    referral_code: str


class AddProjectMemberPayload(DataModel):
    member_id: UUID_TYPE
    role: str


class UpdateProjectMemberRolePayload(DataModel):
    member_id: UUID_TYPE
    role: str


class RemoveProjectMemberPayload(DataModel):
    member_id: UUID_TYPE


class CreateMilestonePayload(DataModel):
    name: str = Field(max_length=255)
    due_date: datetime
    description: Optional[str] = None


class UpdateMilestonePayload(DataModel):
    milestone_id: UUID_TYPE
    name: Optional[str] = Field(max_length=255)
    due_date: Optional[datetime] = None
    description: Optional[str] = None


class CompleteMilestonePayload(DataModel):
    milestone_id: UUID_TYPE


class DeleteMilestonePayload(DataModel):
    milestone_id: UUID_TYPE


class UploadProjectResourcePayload(DataModel):
    file: bytes
    type: Optional[str] = None
    description: Optional[str] = None


class DeleteProjectResourcePayload(DataModel):
    resource_id: UUID_TYPE

# Work Package related payloads


class CreateWorkPackagePayload(DataModel):
    work_package_name: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    complexity_level: str
    credits: float = Field(gt=0)
    example_description: Optional[str] = None
    is_active: bool = True


class UpdateWorkPackagePayload(DataModel):
    work_package_name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    complexity_level: Optional[str] = None
    credits: Optional[float] = Field(gt=0)
    example_description: Optional[str] = None
    is_active: Optional[bool] = None

# Ticket related payloads


class CreateInquiryPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[Priority] = Priority.MEDIUM
    availability: Optional[Availability] = Availability.OPEN


class CreateProjectTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[Priority] = Priority.MEDIUM
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    project_id: UUID_TYPE


class UpdateTicketPayload(DataModel):
    title: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[Priority] = None
    assignee: Optional[UUID_TYPE] = None


class ChangeTicketStatusPayload(DataModel):
    next_status: str
    note: Optional[str] = None


class AssignTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class RemoveTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class AddTicketCommentPayload(DataModel):
    comment_id: UUID_TYPE


class AddTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


class RemoveTicketTagPayload(DataModel):
    tag_id: UUID_TYPE

# Workflow related payloads


class CreateWorkflowPayload(DataModel):
    name: str = Field(max_length=255)
    entity_type: str


class UpdateWorkflowPayload(DataModel):
    name: Optional[str] = Field(max_length=255)
    entity_type: Optional[str] = None


class CreateWorkflowStatusPayload(DataModel):
    key: str


class UpdateWorkflowStatusPayload(DataModel):
    key: Optional[str] = None


class CreateWorkflowTransitionPayload(DataModel):
    src_status_id: UUID_TYPE
    dst_status_id: UUID_TYPE
    rule_code: Optional[str] = None
    condition: Optional[str] = None


class UpdateWorkflowTransitionPayload(DataModel):
    src_status_id: Optional[UUID_TYPE] = None
    dst_status_id: Optional[UUID_TYPE] = None
    rule_code: Optional[str] = None
    condition: Optional[str] = None

# Tag related payloads


class CreateTagPayload(DataModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    target_resource: str
    target_resource_id: Optional[str] = None


class UpdateTagPayload(DataModel):
    code: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Notification related payloads


class MarkNotificationAsReadPayload(DataModel):
    notification_id: UUID_TYPE


class MarkAllNotificationsAsReadPayload(DataModel):
    pass

# Integration related payloads


class UnifiedSyncPayload(DataModel):
    action: str  # "sync" or "proxy"
    entity_type: Optional[str] = None  # "project" or "ticket"
    entity_id: Optional[UUID_TYPE] = None
    provider: str
    direction: Optional[str] = None  # "push" or "pull"
    options: Optional[dict] = None
    method: Optional[str] = None
    params: Optional[dict] = None
