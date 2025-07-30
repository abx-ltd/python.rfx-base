from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import List, Optional, Dict, Any
from datetime import datetime
from rfx_client import logger
from .types import Priority, ProjectStatus, Availability, SyncStatus


class CPOPortalAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles all project, work package, ticket, workflow, tag, integration, and notification operations"""

    # =========== Project Context ============
    @action('estimator-created', resources='project')
    async def create_project_estimator(self, stm, /):
        """Create a new estimator (project draft)"""
        record = self.init_resource(
            "project",
            {
                "name": "",
                "description": None,
                "category": None,
                "priority": Priority.MEDIUM,
                "status": ProjectStatus.DRAFT,
                "start_date": None,
                "target_date": None,
                "free_credit_applied": 0,
                "lead_id": None,
                "referral_code_used": None,
                "status_workflow_id": None,
                "sync_status": SyncStatus.PENDING
            },
            status=ProjectStatus.DRAFT
        )
        await stm.insert(record)
        return record

    @action('project-created', resources='project')
    async def create_project(self, stm, /, data=None):
        """Create a new project directly"""
        if data is None:
            data = {}

        # Create new project with ACTIVE status
        record = self.init_resource(
            "project",
            {
                "name": getattr(data, 'name', ''),
                "description": getattr(data, 'description', None),
                "category": getattr(data, 'category', None),
                "priority": getattr(data, 'priority', Priority.MEDIUM),
                "status": ProjectStatus.ACTIVE,
                "start_date": getattr(data, 'start_date', None),
                "target_date": getattr(data, 'target_date', None),
                "free_credit_applied": 0,
                "lead_id": getattr(data, 'lead_id', None),
                "referral_code_used": None,
                "status_workflow_id": None,
                "sync_status": SyncStatus.PENDING
            }
            # Let database generate UUID automatically
        )
        await stm.insert(record)
        return record

    @action('estimator-converted', resources='project')
    async def convert_estimator_to_project(self, stm, /, data=None):
        """Convert estimator draft to active project"""

    @action('work-package-added', resources='project')
    async def add_work_package_to_estimator(self, stm, /, work_package_id: str, quantity: int):
        """Add work package to estimator"""
        project = self.rootobj

        record = self.init_resource(
            "project-work-package",
            {
                "work_package_id": work_package_id,
                "quantity": quantity,
                "project_id": project._id
            },
            _id=UUID_GENR(),
        )
        await stm.insert(record)
        return record

    @action('credit-cost-calculated', resources='project')
    async def calculate_credit_cost(self, stm, /) -> Dict[str, Any]:
        """Calculate total credit cost"""
        # Query work packages from separate table
        work_packages = await stm.find_all('project-work-package',
                                           where=dict(project_id=self.aggroot.identifier))

        total_credits = 0
        breakdown = {
            "work_packages": [],
            "total_credits": 0,
            "discount_applied": 0,
            "final_cost": 0
        }

        for wp in work_packages:
            # This would typically fetch work package details from repository
            # For now, using placeholder values
            wp_cost = wp.quantity * 10  # Placeholder credit cost
            total_credits += wp_cost
            breakdown["work_packages"].append({
                "work_package_id": wp.work_package_id,
                "quantity": wp.quantity,
                "cost": wp_cost
            })

        # Get project to check free credit applied
        project = self.rootobj
        breakdown["total_credits"] = total_credits
        breakdown["final_cost"] = total_credits - \
            (project.free_credit_applied or 0)

        return breakdown

    @action('referral-code-applied', resources='project')
    async def apply_referral_code(self, stm, /, referral_code: str):
        """Apply referral code to estimator"""
        project = self.rootobj
        await stm.update(project,
                         referral_code_used=referral_code,
                         free_credit_applied=50)  # Placeholder discount

    @action('work-package-quantity-updated', resources='project')
    async def update_work_package_quantity(self, stm, /, work_package_id: str, quantity: int):
        """Update work package quantity in estimator"""
        # Find the work package record
        work_packages = await stm.find_all('project-work-package',
                                           where=dict(
                                               project_id=self.aggroot.identifier,
                                               work_package_id=work_package_id
                                           ))
        if work_packages:
            wp = work_packages[0]
            await stm.update(wp, quantity=quantity, updated_at=datetime.utcnow())

    @action('work-package-removed', resources='project')
    async def remove_work_package_from_estimator(self, stm, /, work_package_id: str):
        """Remove work package from estimator"""
        # Find and delete the work package record
        work_packages = await stm.find_all('project-work-package',
                                           where=dict(
                                               project_id=self.aggroot.identifier,
                                               work_package_id=work_package_id
                                           ))
        for wp in work_packages:
            await stm.invalidate_one('project-work-package', wp._id)

    @action('project-details-updated', resources='project')
    async def update_project_details(self, stm, /, update_data: Dict[str, Any]):
        """Update project details"""
        project = self.rootobj
        await stm.update(project, **serialize_mapping(update_data))

    @action('member-added', resources='project')
    async def add_project_member(self, stm, /, member_id: str, role: str):
        """Add member to project"""
        record = self.init_resource(
            "project-member",
            {
                "member_id": member_id,
                "role": role,
                "project_id": self.aggroot.identifier
            },
            _id=UUID_GENR(),
            added_at=datetime.utcnow()
        )
        await stm.insert(record)

    @action('team-assigned', resources='project')
    async def assign_team_to_project(self, stm, /, team_id: str, role: str):
        """Assign team to project"""
        record = self.init_resource(
            "project-member",
            {
                "team_id": team_id,
                "role": role,
                "project_id": self.aggroot.identifier
            },
            _id=UUID_GENR(),
            assigned_at=datetime.utcnow()
        )
        await stm.insert(record)

    @action('member-role-updated', resources='project')
    async def update_project_member_role(self, stm, /, member_id: str, role: str):
        """Update project member role"""
        members = await stm.find_all('project-member',
                                     where=dict(
                                         project_id=self.aggroot.identifier,
                                         team_id=member_id
                                     ))
        if members:
            member = members[0]
            await stm.update(member, role=role, updated_at=datetime.utcnow())

    @action('member-removed', resources='project')
    async def remove_project_member(self, stm, /, member_id: str):
        """Remove project member"""
        members = await stm.find_all('project-member',
                                     where=dict(
                                         project_id=self.aggroot.identifier,
                                         team_id=member_id
                                     ))
        for member in members:
            await stm.invalidate_one('project-member', member._id)

    @action('milestone-created', resources='project')
    async def create_project_milestone(self, stm, /, name: str, due_date: datetime, description: Optional[str] = None):
        """Create project milestone"""
        record = self.init_resource(
            "project-milestone",
            {
                "name": name,
                "due_date": due_date,
                "description": description,
                "project_id": self.aggroot.identifier
            },
            _id=UUID_GENR(),
            status="PENDING",
            created_at=datetime.utcnow()
        )
        await stm.insert(record)

    @action('milestone-updated', resources='project')
    async def update_project_milestone(self, stm, /, milestone_id: str, update_data: Dict[str, Any]):
        """Update project milestone"""
        milestone = await stm.fetch('project-milestone', milestone_id)
        if milestone and milestone.project_id == self.aggroot.identifier:
            await stm.update(milestone, **serialize_mapping(update_data), updated_at=datetime.utcnow())

    @action('milestone-completed', resources='project')
    async def complete_project_milestone(self, stm, /, milestone_id: str):
        """Complete project milestone"""
        milestone = await stm.fetch('project-milestone', milestone_id)
        if milestone and milestone.project_id == self.aggroot.identifier:
            await stm.update(milestone, status="COMPLETED", completed_at=datetime.utcnow())

    @action('milestone-uncompleted', resources='project')
    async def uncomplete_project_milestone(self, stm, /, milestone_id: str):
        """Uncomplete project milestone"""
        milestone = await stm.fetch('project-milestone', milestone_id)
        if milestone and milestone.project_id == self.aggroot.identifier:
            await stm.update(milestone, status="PENDING", uncompleted_at=datetime.utcnow())

    @action('milestone-deleted', resources='project')
    async def delete_project_milestone(self, stm, /, milestone_id: str):
        """Delete project milestone"""
        milestone = await stm.fetch('project-milestone', milestone_id)
        if milestone and milestone.project_id == self.aggroot.identifier:
            await stm.invalidate_one('project-milestone', milestone_id)

    @action('resource-uploaded', resources='project')
    async def upload_project_resource(self, stm, /, file: bytes, type: Optional[str] = None, description: Optional[str] = None) -> str:
        """Upload project resource"""
        resource_id = UUID_GENR()
        record = self.init_resource(
            "project-resource",
            {
                "type": type,
                "description": description,
                "size": len(file),
                "project_id": self.aggroot.identifier
            },
            _id=resource_id,
            uploaded_at=datetime.utcnow()
        )
        await stm.insert(record)
        return str(resource_id)

    @action('resource-deleted', resources='project')
    async def delete_project_resource(self, stm, /, resource_id: str):
        """Delete project resource"""
        await stm.invalidate_one("project-resource", resource_id)

    # =========== Tag Context ============
    @action("tag-created", resources="tag")
    async def create_tag(self, stm, /, data):
        """Create a new tag"""
        record = self.init_resource(
            "tag",
            serialize_mapping(data),
        )
        await stm.insert(record)
        return record

    @action("tag-updated", resources="tag")
    async def update_tag(self, stm, /, data):
        """Update tag"""
        tag = self.rootobj
        await stm.update(tag, **serialize_mapping(data))
        return tag

    # =========== Ticket Context ============
    @action("ticket-type-created", resources="ticket")
    async def create_ticket_type(self, stm, /, data):
        """Create a new ticket type"""
        record = self.init_resource(
            "ref--ticket-type",
            serialize_mapping(data),
        )
        await stm.insert(record)
        return record

    @action('inquiry-created', resources='ticket')
    async def create_inquiry(self, stm, /, data):
        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status="DRAFT",
            availability=Availability.OPEN,
        )
        await stm.insert(record)
        return record

    @action('ticket-created', resources='ticket')
    async def create_ticket(self, stm, /, data):
        """Create a new ticket tied to project"""
        # ticket_data = data.model_dump(exclude={'project_id'})
        ticket_data = serialize_mapping(data)
        ticket_data.update({
            "_id": self.aggroot.identifier,
            "status": "DRAFT",
            "availability": Availability.OPEN,
            "sync_status": SyncStatus.PENDING
        })
        ticket = self.init_resource("ticket", ticket_data)

        logger.info(f"Ticket data: {ticket}")

        await stm.insert(ticket)

        await stm.insert(self.init_resource("project-ticket", {
            "project_id": data.project_id,
            "ticket_id": ticket._id
        }))

        return ticket

    @action('ticket-updated', resources='ticket')
    async def update_ticket_info(self, stm, /, data):
        """Update ticket information"""
        ticket = self.rootobj
        await stm.update(ticket, **serialize_mapping(data))
        return ticket

    @action('ticket-closed', resources='ticket')
    async def close_ticket(self, stm, /):
        """Close ticket"""
        ticket = self.rootobj
        await stm.update(ticket, availability=Availability.CLOSED)
        return ticket

    @action('ticket-reopened', resources='ticket')
    async def reopen_ticket(self, stm, /):
        """Reopen ticket"""
        ticket = self.rootobj
        await stm.update(ticket, availability=Availability.AVAILABLE)
        return ticket

    @action('ticket-status-changed', resources='ticket')
    async def change_ticket_status(self, stm, /, next_status: str, note: Optional[str] = None):
        """Change ticket status using workflow"""
        ticket = self.rootobj

        # Create status transition record
        status_record = self.init_resource(
            "ticket-status",
            {
                "ticket_id": ticket._id,
                "src_state": ticket.status,
                "dst_state": next_status,
                "note": note
            },
            _id=UUID_GENR()
        )
        await stm.insert(status_record)

        # Update ticket status
        await stm.update(ticket, status=next_status)
        return ticket

    @action('member-assigned-to-ticket', resources='ticket')
    async def assign_member_to_ticket(self, stm, /, member_id: str):
        """Assign member to ticket"""
        record = self.init_resource(
            "ticket-assignee",
            {
                "ticket_id": self.aggroot.identifier,
                "member_id": member_id,
                "role": "ASSIGNEE"
            },
            _id=UUID_GENR(),
            assigned_at=datetime.utcnow()
        )
        await stm.insert(record)
        return record

    @action('member-removed-from-ticket', resources='ticket')
    async def remove_member_from_ticket(self, stm, /, member_id: str):
        """Remove member from ticket"""
        assignees = await stm.find_all('ticket-assignee',
                                       where=dict(
                                           ticket_id=self.aggroot.identifier,
                                           member_id=member_id
                                       ))
        for assignee in assignees:
            await stm.invalidate_one('ticket-assignee', assignee._id)
        return {"removed": True}

    @action('comment-added-to-ticket', resources='ticket')
    async def add_ticket_comment(self, stm, /, comment_id: str):
        """Add comment to ticket"""
        record = self.init_resource(
            "ticket-comment",
            {
                "ticket_id": self.aggroot.identifier,
                "comment_id": comment_id
            },
            _id=UUID_GENR(),
            added_at=datetime.utcnow()
        )
        await stm.insert(record)
        return record

    @action('participant-added-to-ticket', resources='ticket')
    async def add_ticket_participant(self, stm, /, participant_id: str):
        """Add participant to ticket"""
        record = self.init_resource(
            "ticket-participants",
            {
                "ticket_id": self.aggroot.identifier,
                "participant_id": participant_id
            },
            _id=UUID_GENR()
        )
        await stm.insert(record)
        return record

    @action('tag-added-to-ticket', resources='ticket')
    async def add_ticket_tag(self, stm, /, tag_id: str):
        """Add tag to ticket"""
        record = self.init_resource(
            "ticket-tag",
            {
                "ticket_id": self.aggroot.identifier,
                "tag_id": tag_id
            },
            _id=UUID_GENR()
        )
        await stm.insert(record)
        return record

    @action('tag-removed-from-ticket', resources='ticket')
    async def remove_ticket_tag(self, stm, /, tag_id: str):
        """Remove tag from ticket"""
        tags = await stm.find_all('ticket-tag',
                                  where=dict(
                                      ticket_id=self.aggroot.identifier,
                                      tag_id=tag_id
                                  ))
        for tag in tags:
            await stm.invalidate_one('ticket-tag', tag._id)
        return {"removed": True}

    # =========== Work Package Context ============
    @action('work-package-created', resources='work-package')
    async def create_work_package(self, stm, /, data):
        """Create new work package"""
        record = self.init_resource(
            "work-package",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-package-updated', resources='work-package')
    async def update_work_package(self, stm, /, data):
        """Update work package details"""
        work_package = self.rootobj
        await stm.update(work_package, **serialize_mapping(data))
        return work_package

    @action('work-package-invalidated', resources='work-package')
    async def invalidate_work_package(self, stm, /):
        """Invalidate work package"""
        work_package = self.rootobj
        await stm.invalidate(work_package)
        return work_package

    @action('work-package-type-created', resources='work-package')
    async def create_work_package_type(self, stm, /, data):
        """Create new work package type"""
        record = self.init_resource(
            "ref--work-package-type",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-package-deliverable-created', resources='work-package')
    async def create_work_package_deliverable(self, stm, /, data):
        """Create new work package deliverable"""
        record = self.init_resource(
            "work-package-deliverable",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

        # """ Fetch exactly 1 item from the data store using either a query object or where statements
        #     Raises an error if there are 0 or multiple results """
        # q = BackendQuery.create(q, **query, limit=1, offset=0)
        # if q.limit != 1 or q.offset != 0:
        #     raise ValueError(f'Invalid find_one query: {q}')

        # try:
        #     item = await self.connector.find_one(model_name, q)
        #     return self._wrap_item(model_name, item)
        # except ItemNotFoundError:
        #     return None

    @action('work-package-deliverable-invalidated', resources='work-package')
    async def invalidate_work_package_deliverable(self, stm, /, data):
        """Invalidate work package deliverable"""
        deliverable = await stm.find_one('work-package-deliverable', where=dict(
            work_package_id=self.rootobj._id,
            _id=data.deliverable_id
        ))
        if deliverable:
            await stm.invalidate_one('work-package-deliverable', deliverable._id)

    # =========== Work Item Context ============

    @action('work-item-created', resources='work-item')
    async def create_work_item(self, stm, /, data):
        """Create new work item"""
        record = self.init_resource(
            "work-item",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-item-added-to-work-package', resources='work-package')
    async def add_work_item_to_work_package(self, stm, /, work_item_id):
        """Add work item to work package"""
        work_package = self.rootobj
        data = {
            "work_package_id": work_package._id,
            "work_item_id": work_item_id
        }
        record = self.init_resource(
            "work-package-work-item",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    # =========== Integration Context ============
    @action('integration-sync', resources='integration')
    async def unified_sync(self, stm, /, data):
        """Unified sync method for integrations"""

    # =========== Notification Context ============
    @action('notification-marked-read', resources='notification')
    async def mark_notification_as_read(self, stm, /, notification_id: str):
        """Mark notification as read"""

    @action('all-notifications-marked-read', resources='notification')
    async def mark_all_notifications_as_read(self, stm, /):
        """Mark all notifications as read"""
