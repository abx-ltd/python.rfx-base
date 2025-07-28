from fastapi import Request
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID, IntegerField, FloatField, DatetimeField
from typing import Optional

from .state import CPOPortalStateManager
from .domain import CPOPortalDomain
from .policy import CPOPortalPolicyManager
from .types import Priority, ProjectStatus, Availability, SyncStatus


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
    description: str = StringField("Description")
    type: str = StringField("Type")
    complexity_level: str = StringField("Complexity Level")
    credits: float = FloatField("Credits")
    is_active: bool = BooleanField("Is Active")
    example_description: str = StringField("Example Description")


@resource('ref--work-package-type')
class RefWorkPackageTypeQuery(DomainQueryResource):
    """Work package type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


@resource('ref--work-package-complexity')
class RefWorkPackageComplexityQuery(DomainQueryResource):
    """Work package complexity reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")


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
    """Inquiry listing queries - Lists inquiries created by current user"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    title: str = StringField("Title")
    type: str = StringField("Type")
    status: str = StringField("Status")
    availability: Availability = EnumField("Availability")

    @endpoint('inquiry-listing')
    async def list_inquiries(self, request: Request):
        """List inquiries created by current user"""
        context = self.get_context()
        user_id = context.user_id

        # Get inquiries where _creator is current user and project_id is None
        inquiries = await self.find_all(
            where=dict(
                _creator=user_id,
                project_id=None
            ),
            order_by="_updated DESC"
        )

        # Transform to include additional info
        result = []
        for inquiry in inquiries:
            # Get participants count
            participants = await self.find_all(
                'ticket-assignee',
                where=dict(ticket_id=inquiry._id)
            )

            # Get replies count (comments)
            replies = await self.find_all(
                'ticket-comment',
                where=dict(ticket_id=inquiry._id)
            )

            result.append({
                "type": inquiry.type,
                "inquiry": inquiry,
                "participants": len(participants),
                "repliesCount": len(replies),
                "activity": inquiry._updated,
                "status": inquiry.availability.value
            })

        return result


@resource('ticket-listing')
class TicketListingQuery(DomainQueryResource):
    """Ticket listing queries - Lists tickets by project"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    title: str = StringField("Title")
    type: str = StringField("Type")
    status: str = StringField("Status")
    availability: Availability = EnumField("Availability")
    project_id: UUID_TYPE = UUIDField("Project ID")

    @endpoint('ticket-listing')
    async def list_tickets(self, request: Request):
        """List tickets by project"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return []

        # Get tickets for specific project
        tickets = await self.find_all(
            where=dict(
                project_id=project_id
            ),
            order_by="_updated DESC"
        )

        # Transform to include additional info
        result = []
        for ticket in tickets:
            # Get participants count
            participants = await self.find_all(
                'ticket-assignee',
                where=dict(ticket_id=ticket._id)
            )

            # Get replies count (comments)
            replies = await self.find_all(
                'ticket-comment',
                where=dict(ticket_id=ticket._id)
            )

            result.append({
                "type": ticket.type,
                "ticket": ticket,
                "participants": len(participants),
                "repliesCount": len(replies),
                "activity": ticket._updated,
                "status": ticket.availability.value
            })

        return result


@resource('ticket-detail')
class TicketDetailQuery(DomainQueryResource):
    """Ticket detail queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = False
        allow_meta_view = True

    title: str = StringField("Title")
    description: str = StringField("Description")
    type: str = StringField("Type")
    priority: Priority = EnumField("Priority")
    status: str = StringField("Status")
    availability: Availability = EnumField("Availability")
    project_id: UUID_TYPE = UUIDField("Project ID")
    assignee: UUID_TYPE = UUIDField("Assignee")
    parent_id: UUID_TYPE = UUIDField("Parent ID")

    @endpoint('ticket-detail')
    async def get_ticket_detail(self, request: Request):
        """Get ticket detail with comments and status history"""
        ticket_id = request.path_params.get('ticket_id')
        if not ticket_id:
            return None

        # Get ticket
        ticket = await self.fetch('ticket', ticket_id)
        if not ticket:
            return None

        # Get comments
        comments = await self.find_all(
            'ticket-comment',
            where=dict(ticket_id=ticket_id)
        )

        # Get status history
        status_history = await self.find_all(
            'ticket-status',
            where=dict(ticket_id=ticket_id),
            order_by="_created ASC"
        )

        return {
            "ticket": ticket,
            "comments": comments,
            "status_history": status_history
        }


@resource('ticket-status-history-listing')
class TicketStatusHistoryQuery(DomainQueryResource):
    """Ticket status history queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    src_state: str = StringField("Source State")
    dst_state: str = StringField("Destination State")
    note: str = StringField("Note")

    @endpoint('ticket-status-history-listing')
    async def list_ticket_status_history(self, request: Request):
        """List ticket status history"""
        ticket_id = request.path_params.get('ticket_id')
        if not ticket_id:
            return []

        status_transitions = await self.find_all(
            'ticket-status',
            where=dict(ticket_id=ticket_id),
            order_by="_created ASC"
        )

        return status_transitions


@resource('ticket-comment-listing')
class TicketCommentQuery(DomainQueryResource):
    """Ticket comment queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    comment_id: UUID_TYPE = UUIDField("Comment ID")

    @endpoint('ticket-comment-listing')
    async def list_ticket_comments(self, request: Request):
        """List comments for a ticket"""
        ticket_id = request.path_params.get('ticket_id')
        if not ticket_id:
            return []

        comments = await self.find_all(
            'ticket-comment',
            where=dict(ticket_id=ticket_id),
            order_by="_created ASC"
        )

        return comments


@resource('ticket-tag-listing')
class TicketTagQuery(DomainQueryResource):
    """Ticket tag queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    tag_id: UUID_TYPE = UUIDField("Tag ID")

    @endpoint('ticket-tag-listing')
    async def list_ticket_tags(self, request: Request):
        """List tags for a ticket"""
        ticket_id = request.path_params.get('ticket_id')
        if not ticket_id:
            return []

        tags = await self.find_all(
            'ticket-tag',
            where=dict(ticket_id=ticket_id)
        )

        return tags


@resource('ticket-type-listing')
class TicketTypeQuery(DomainQueryResource):
    """Ticket type queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    icon_color: str = StringField("Icon Color")
    is_active: bool = BooleanField("Is Active")

    @endpoint('ticket-type-listing')
    async def list_ticket_types(self, request: Request):
        """List available ticket types/categories"""
        ticket_types = await self.find_all(
            'ref--ticket-type',
            where=dict(is_active=True),
            order_by="name ASC"
        )

        return ticket_types


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


@resource('ref--ticket-type')
class RefTicketTypeQuery(DomainQueryResource):
    """Ticket type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    icon_color: str = StringField("Icon Color")
    is_active: bool = BooleanField("Is Active")


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


@resource('ref--notification-type')
class RefNotificationTypeQuery(DomainQueryResource):
    """Notification type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


# Reference Queries
@resource('ref--project-category')
class RefProjectCategoryQuery(DomainQueryResource):
    """Project category reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


@resource('ref--project-role')
class RefProjectRoleQuery(DomainQueryResource):
    """Project role reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_default: bool = BooleanField("Is Default")
