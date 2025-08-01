import select
from .types import Priority, ProjectStatus, Availability, SyncStatus
from .policy import CPOPortalPolicyManager
from .domain import CPOPortalDomain
from .state import CPOPortalStateManager
from typing import Optional
from fastapi import Request
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID, IntegerField, FloatField, DatetimeField, ListField, DictField, ArrayField
from . import scope


default_exclude_fields = ["realm", "deleted", "etag",
                          "created", "updated", "creator", "updater"]


class CPOPortalQueryManager(DomainQueryManager):
    __data_manager__ = CPOPortalStateManager
    __policymgr__ = CPOPortalPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = CPOPortalDomain.Meta.prefix
        tags = CPOPortalDomain.Meta.tags


resource = CPOPortalQueryManager.register_resource
endpoint = CPOPortalQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


# Project Queries
@resource('project')
class ProjectQuery(DomainQueryResource):
    """Project queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    name: str = StringField("Project Name")
    description: str = StringField("Description")
    category: str = StringField("Category")
    priority: Priority = EnumField("Priority")
    status: str = StringField("Status")
    start_date: str = DatetimeField("Start Date")
    target_date: str = DatetimeField("Target Date")
    free_credit_applied: int = IntegerField("Free Credit Applied")
    lead_id: UUID_TYPE = UUIDField("Lead ID")
    referral_code_used: UUID_TYPE = UUIDField("Referral Code Used")
    status_workflow_id: UUID_TYPE = UUIDField("Status Workflow ID")
    sync_status: SyncStatus = EnumField("Sync Status")


@resource('project-milestone')
class ProjectMilestoneQuery(DomainQueryResource):
    """Project milestone queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    project_id: UUID_TYPE = UUIDField("Project ID")
    name: str = StringField("Milestone Name")
    description: str = StringField("Description")
    due_date: str = DatetimeField("Due Date")
    completed_at: str = DatetimeField("Completed At")


@resource('project-member')
class ProjectMemberQuery(DomainQueryResource):
    """Project member queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    project_id: UUID_TYPE = UUIDField("Project ID")
    member_id: UUID_TYPE = UUIDField("Member ID")
    role: str = StringField("Role")
    permission: str = StringField("Permission")


@resource('project-work-package')
class ProjectWorkPackageQuery(DomainQueryResource):
    """Project work package queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    project_id: UUID_TYPE = UUIDField("Project ID")
    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    wp_code: str = StringField("Work Package Code")
    quantity: int = IntegerField("Quantity")


@resource('work-item-listing')
class WorkItemListingQuery(DomainQueryResource):
    """Work item listing queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_work-item-listing"

        scope_required = scope.WorkItemListingScopeSchema

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")
    work_item_name: str = StringField("Work Item Name")
    work_item_description: str = StringField("Work Item Description")
    work_item_type_code: str = StringField("Work Item Type Code")
    work_item_type_name: str = StringField("Work Item Type Name")


@resource('project-status')
class ProjectStatusQuery(DomainQueryResource):
    """Project status queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    project_id: UUID_TYPE = UUIDField("Project ID")
    src_state: str = StringField("Source State")
    dst_state: str = StringField("Destination State")
    note: str = StringField("Note")

# Work Package Queries


@resource('work-package')
class WorkPackageQuery(DomainQueryResource):
    """Work package queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    work_package_name: str = StringField("Work Package Name")
    type: str = StringField("Type")
    complexity_level: str = StringField("Complexity Level")
    credits: float = FloatField("Credits")
    is_custom: bool = BooleanField("Is Custom")


@resource('work-package-type')
class RefWorkPackageTypeQuery(DomainQueryResource):
    """Work package type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--work-package-type"

    name: str = StringField("Name")
    description: str = StringField("Description")


@resource('work-package-complexity')
class RefWorkPackageComplexityQuery(DomainQueryResource):
    """Work package complexity reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--work-package-complexity"

    code: str = StringField("Code")
    name: str = StringField("Name")


@resource('work-package-detail')
class WorkPackageDetailQuery(DomainQueryResource):
    """Work package detail queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "_work-package-detail"

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_package_name: str = StringField("Work Package Name")
    type_list: list[str] = ArrayField("Type List")


# Ticket Queries
@resource('ticket')
class TicketQuery(DomainQueryResource):
    """Ticket queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    title: str = StringField("Title")
    priority: Priority = EnumField("Priority")
    type: str = StringField("Type")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    assignee: UUID_TYPE = UUIDField("Assignee")
    status: str = StringField("Status")
    workflow_id: UUID_TYPE = UUIDField("Workflow ID")
    availability: Availability = EnumField("Availability")
    sync_status: SyncStatus = EnumField("Sync Status")
    project_id: UUID_TYPE = UUIDField("Project ID")


@resource('inquiry-listing')
class InquiryListingQuery(DomainQueryResource):
    """Inquiry listing queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_list_view = True
        allow_item_view = False
        allow_meta_view = True
        backend_model = "_inquiry-listing"

    type: str = StringField("Type")
    type_icon_color: str = StringField("Type Icon Color")
    title: str = StringField("Title")
    tag_names: list[str] = ArrayField("Tag Names")
    availability: Availability = EnumField("Availability")


@resource('ticket-status')
class TicketStatusQuery(DomainQueryResource):
    """Ticket status queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    src_state: str = StringField("Source State")
    dst_state: str = StringField("Destination State")
    note: str = StringField("Note")


@resource('ticket-comment')
class TicketCommentQuery(DomainQueryResource):
    """Ticket comment queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    comment_id: UUID_TYPE = UUIDField("Comment ID")


@resource('ticket-assignee')
class TicketAssigneeQuery(DomainQueryResource):
    """Ticket assignee queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    member_id: UUID_TYPE = UUIDField("Member ID")
    role: str = StringField("Role")


@resource('ticket-participants')
class TicketParticipantsQuery(DomainQueryResource):
    """Ticket participants queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    participant_id: UUID_TYPE = UUIDField("Participant ID")


@resource('ticket-type')
class RefTicketTypeQuery(DomainQueryResource):
    """Ticket type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        excluded_fields = default_exclude_fields
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--ticket-type"

    is_active: bool = BooleanField("Is Active")
    is_inquiry: bool = BooleanField("Is Inquiry")


# Workflow Queries
@resource('workflow')
class WorkflowQuery(DomainQueryResource):
    """Workflow queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    entity_type: str = EnumField("Entity Type")
    name: str = StringField("Name")


@resource('workflow-status')
class WorkflowStatusQuery(DomainQueryResource):
    """Workflow status queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    workflow_id: UUID_TYPE = UUIDField("Workflow ID")
    key: str = StringField("Key")
    is_start: bool = BooleanField("Is Start")
    is_end: bool = BooleanField("Is End")


@resource('workflow-transition')
class WorkflowTransitionQuery(DomainQueryResource):
    """Workflow transition queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    workflow_id: UUID_TYPE = UUIDField("Workflow ID")
    src_status_id: UUID_TYPE = UUIDField("Source Status ID")
    dst_status_id: UUID_TYPE = UUIDField("Destination Status ID")
    rule_code: str = StringField("Rule Code")
    condition: str = StringField("Condition")


# Tag Queries
@resource('tag')
class TagQuery(DomainQueryResource):
    """Tag queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")
    target_resource: str = StringField("Target Resource")
    target_resource_id: str = StringField("Target Resource ID")


# Integration Queries
@resource('integration')
class IntegrationQuery(DomainQueryResource):
    """Integration queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    entity_type: str = StringField("Entity Type")
    entity_id: UUID_TYPE = UUIDField("Entity ID")
    provider: str = StringField("Provider")
    external_id: str = StringField("External ID")
    external_url: str = StringField("External URL")
    status: SyncStatus = EnumField("Status")


# Notification Queries
@resource('notification')
class NotificationQuery(DomainQueryResource):
    """Notification queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    user_id: UUID_TYPE = UUIDField("User ID")
    source_entity_type: str = StringField("Source Entity Type")
    source_entity_id: UUID_TYPE = UUIDField("Source Entity ID")
    message: str = StringField("Message")
    type: str = StringField("Type")
    is_read: bool = BooleanField("Is Read")


@resource('notification-type')
class RefNotificationTypeQuery(DomainQueryResource):
    """Notification type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--notification-type"

    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


# Reference Queries
@resource('project-category')
class RefProjectCategoryQuery(DomainQueryResource):
    """Project category reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--project-category"

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


@resource('project-role')
class RefProjectRoleQuery(DomainQueryResource):
    """Project role reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--project-role"

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_default: bool = BooleanField("Is Default")
