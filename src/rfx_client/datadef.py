from typing import Optional

from pydantic import Field
from datetime import datetime
from fluvius.data import DataModel, UUID_TYPE

from .types import PriorityEnum, AvailabilityEnum, SyncStatusEnum, ContactMethodEnum
from typing import Any, Dict

# Project related payloads


class CreateProjectEstimatorPayload(DataModel):
    """Payload for creating project estimator"""

    name: Optional[str] = Field(max_length=255, default="")
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[PriorityEnum] = None


class CreateProjectPayload(DataModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    start_date: datetime = Field(default_factory=datetime.now)
    duration: str = Field(default="P9D")


class UpdateProjectPayload(DataModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    duration: Optional[str] = None


class DeleteProjectPayload(DataModel):
    pass


# Project BDM Contact related payloads


class CreateProjectBDMContactPayload(DataModel):
    contact_method: Optional[list[ContactMethodEnum]] = None
    message: Optional[str] = None
    meeting_time: Optional[datetime] = None
    status: Optional[str] = None


class UpdateProjectBDMContactPayload(DataModel):
    bdm_contact_id: UUID_TYPE
    contact_method: Optional[list[ContactMethodEnum]] = None
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
    priority: Optional[PriorityEnum] = PriorityEnum.MEDIUM
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    availability: str = "OPEN"
    status: Optional[str] = "DRAFT"
    sync_status: Optional[SyncStatusEnum] = SyncStatusEnum.PENDING
    sync_linear: bool = False


class AddCustomWorkPackageToProjectPayload(DataModel):
    project_work_package_id: UUID_TYPE


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


class UpdateProjectMemberPayload(DataModel):
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
    complexity_level: Optional[int] = None


class UpdateWorkPackagePayload(DataModel):
    work_package_name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    example_description: Optional[str] = None
    complexity_level: Optional[int] = None


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


class CreateCustomWorkPackagePayload(DataModel):
    work_package_name: str = Field(max_length=255)
    description: Optional[str] = None
    example_description: Optional[str] = None
    complexity_level: Optional[int] = None


class UpdateProjectWorkPackagePayload(DataModel):
    project_work_package_id: UUID_TYPE
    work_package_name: Optional[str] = Field(max_length=255)
    work_package_description: Optional[str] = None
    work_package_example_description: Optional[str] = None
    work_package_is_custom: Optional[bool] = None
    work_package_complexity_level: Optional[int] = None


class UpdateProjectWorkPackageWithWorkItemsPayload(DataModel):
    project_work_package_id: UUID_TYPE
    work_package_name: Optional[str] = Field(max_length=255)
    work_package_description: Optional[str] = None
    work_package_example_description: Optional[str] = None
    work_package_is_custom: Optional[bool] = None
    work_package_complexity_level: Optional[int] = None
    work_item_ids: list[UUID_TYPE]


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


class CreditUsageSummaryPayload(DataModel):
    organization_id: UUID_TYPE


# Project Integration related payloads


class CreateProjectIntegrationPayload(DataModel):
    provider: str
    external_id: str
    external_url: str


class UpdateProjectIntegrationPayload(DataModel):
    provider: str
    external_id: str
    external_url: str


class RemoveProjectIntegrationPayload(DataModel):
    provider: str
    external_id: str


class SyncProjectIntegrationPayload(DataModel):
    provider: str
    external_id: str
    external_url: str


# ProjectMilestone Integration related payloads


class CreateProjectMilestoneIntegrationPayload(DataModel):
    provider: str
    external_id: str
    external_url: Optional[str] = None
    milestone_id: UUID_TYPE


class UpdateProjectMilestoneIntegrationPayload(DataModel):
    provider: str
    external_id: str
    external_url: Optional[str] = None
    milestone_id: UUID_TYPE


class RemoveProjectMilestoneIntegrationPayload(DataModel):
    provider: str
    external_id: str
    milestone_id: UUID_TYPE


# =============== Ticket Datadef ===============


# ---------- Inquiry (Ticket Context) ----------
class CreateInquiryPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[PriorityEnum] = PriorityEnum.MEDIUM
    availability: Optional[AvailabilityEnum] = AvailabilityEnum.CLOSED


# ---------- Ticket (Ticket Context) ----------
class CreateTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: str
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    availability: Optional[AvailabilityEnum] = AvailabilityEnum.OPEN
    project_id: str


class UpdateTicketPayload(DataModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    assignee: Optional[UUID_TYPE] = None
    availability: Optional[AvailabilityEnum] = None
    status: Optional[str] = None


class RemoveTicketPayload(DataModel):
    ticket_id: UUID_TYPE


class SyncAllTicketsToLinearPayload(DataModel):
    project_id: UUID_TYPE


# ---------- Ticket Assignee (Ticket Context) ----------
class AssignTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class RemoveTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


# ---------- Ticket Participant (Ticket Context) ----------
class AddTicketParticipantPayload(DataModel):
    participant_id: UUID_TYPE


class RemoveTicketParticipantPayload(DataModel):
    participant_id: UUID_TYPE


# ---------- Ticket Tag (Ticket Context) ----------
class AddTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


class RemoveTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


# ---------- Ticket Type (Ticket Context) ----------
class CreateTicketTypePayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: bool = True
    is_inquiry: bool = False


class UpdateTicketTypePayload(DataModel):
    ticket_type_id: UUID_TYPE
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: Optional[bool] = None
    is_inquiry: Optional[bool] = None


class DeleteTicketTypePayload(DataModel):
    ticket_type_id: UUID_TYPE = None


# Tag related payloads
class CreateTagPayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    target_resource: str


class UpdateTagPayload(DataModel):
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    target_resource: Optional[str] = None
    is_active: Optional[bool] = None


# ---------- Status Context ----------


class CreateStatusPayload(DataModel):
    name: str
    description: Optional[str] = None
    entity_type: str
    is_active: bool = True


class CreateStatusKeyPayload(DataModel):
    key: str
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_final: bool = False


class CreateStatusTransitionPayload(DataModel):
    src_status_key_id: UUID_TYPE
    dst_status_key_id: UUID_TYPE
    condition: Optional[dict] = None


# ------------- Ticket Integration-----------


class CreateTicketIntegrationPayload(DataModel):
    """Payload for creating ticket integration"""

    provider: str = "linear"
    external_id: str
    external_url: Optional[str] = None


class UpdateTicketIntegrationPayload(DataModel):
    """Payload for updating ticket integration"""

    provider: str = "linear"
    external_id: str
    external_url: Optional[str] = None


class RemoveTicketIntegrationPayload(DataModel):
    """Payload for removing ticket integration"""

    provider: str = "linear"
    external_id: str


class SyncTicketIntegrationPayload(DataModel):
    """Payload for syncing ticket integration"""

    provider: str = "linear"
    external_id: Optional[str] = None
    external_url: Optional[str] = None


# ---------- Comment Context ----------


class CreateCommentPayload(DataModel):
    content: str


class UpdateCommentPayload(DataModel):
    content: str


class DeleteCommentPayload(DataModel):
    pass


class ReplyToCommentPayload(DataModel):
    content: str


class CreateCommentIntegrationPayload(DataModel):
    """Payload for creating comment integration"""

    provider: str
    external_id: str
    external_url: Optional[str] = None
    comment_id: UUID_TYPE
    source: Optional[str] = None  # e.g., 'user', 'system', 'linear'


class UpdateCommentIntegrationPayload(DataModel):
    """Payload for updating comment integration"""

    provider: str
    external_id: str
    external_url: Optional[str] = None


class RemoveCommentIntegrationPayload(DataModel):
    """Payload for removing comment integration"""

    provider: str
    external_id: str
    comment_id: UUID_TYPE


class SyncCommentFromWebhookPayload(DataModel):
    """Payload for syncing comment from webhook"""

    action: str = Field(..., description="Action: create, update, delete")
    provider: str = Field(..., description="Provider name: linear, jira, etc.")
    external_id: str = Field(..., description="External comment ID")
    external_data: Dict[str, Any] = Field(..., description="Raw webhook data")
    target_id: Optional[str] = Field(None, description="Parent resource ID (issue_id)")
    target_type: Optional[str] = Field(None, description="Parent resource type (issue)")


class SyncTicketFromWebhookPayload(DataModel):
    """Payload for syncing ticket from webhook"""

    action: str = Field(..., description="Action: create, update, delete")
    provider: str = Field(..., description="Provider name")
    external_id: str = Field(..., description="External ticket ID")
    external_data: Dict[str, Any] = Field(..., description="Raw webhook data")


class SyncProjectFromWebhookPayload(DataModel):
    """Payload for syncing project from webhook"""

    action: str = Field(..., description="Action: create, update, delete")
    provider: str = Field(..., description="Provider name")
    external_id: str = Field(..., description="External project ID")
    external_data: Dict[str, Any] = Field(..., description="Raw webhook data")


class AttachmentUploadPayload(DataModel):
    """Payload for presigning attachment upload"""

    file_name: str
    file_type: str
    file_size: int


class AttachFileToCommentPayload(DataModel):
    file_url: str
    file_name: str
    file_type: str
    file_size: int
    file_extension: Optional[str] = None

    is_image: Optional[bool] = False
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    thumbnail_url: Optional[str] = None


class UpdateAttachmentPayload(DataModel):
    attachment_id: UUID_TYPE
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    upload_status: Optional[str] = None


class DeleteAttachmentPayload(DataModel):
    attachment_id: UUID_TYPE


class CreateReactionCommentPayload(DataModel):
    reaction_type: str  # e.g., like, helpful, insightful, funny
