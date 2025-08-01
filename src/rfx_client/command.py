from datetime import datetime
from hmac import new
from fluvius.data import serialize_mapping, DataModel, UUID_GENR

from .domain import CPOPortalDomain
from . import datadef, config

processor = CPOPortalDomain.command_processor
Command = CPOPortalDomain.Command


# ---------- Project Context ----------

class CreateEstimator(Command):
    """Create Estimator - Creates a new estimator (project draft)"""

    class Meta:
        key = "create-estimator"
        resources = ("project",)
        tags = ["project", "estimator"]
        auth_required = True
        description = "Create a new estimator (project draft)"
        new_resource = True

    Data = datadef.CreateProjectEstimatorPayload

    async def _process(self, agg, stm, payload):
        """Create a new project estimator draft"""
        result = await agg.create_project_estimator()
        yield agg.create_response(serialize_mapping(result), _type="project-response")


class CreateProject(Command):
    """Create Project - Creates a new project - this is a conversion from estimator"""

    class Meta:
        key = "create-project"
        resources = ("project",)
        tags = ["project"]
        auth_required = True
        description = "Create a new project directly"
        new_resource = True

    Data = datadef.CreateProjectPayload

    async def _process(self, agg, stm, payload):
        """Create a new project directly"""
        result = await agg.create_project(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-response")


class AddWorkPackageToEstimator(Command):
    """Add Work Package to Estimator - Adds a specific Work Package to the estimator draft"""

    class Meta:
        key = "add-work-package-to-estimator"
        resources = ("project",)
        tags = ["project", "work-package"]
        auth_required = True
        description = "Add work package to current estimator draft"

    Data = datadef.AddWorkPackageToProjectPayload

    async def _process(self, agg, stm, payload):
        """Add work package to estimator draft"""
        await agg.add_work_package_to_estimator(data=payload)



# class ApplyReferralCodeToEstimator(Command):
#     """Apply Referral Code to Estimator - Applies a referral code to the current estimator draft"""

#     class Meta:
#         key = "apply-referral-code"
#         resources = ("project",)
#         tags = ["project", "referral"]
#         auth_required = True
#         description = "Apply referral code to current estimator draft"

#     Data = datadef.ApplyReferralCodePayload

#     async def _process(self, agg, stm, payload):
#         """Apply referral code to estimator"""
#         await agg.apply_referral_code(payload.referral_code)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UpdateWorkPackageQuantity(Command):
#     """Update Work Package Quantity - Updates quantity of a Work Package in the current estimator draft"""

#     class Meta:
#         key = "update-work-package-from-estimator"
#         resources = ("project",)
#         tags = ["project", "work-package"]
#         auth_required = True
#         description = "Update work package quantity in estimator"

#     Data = datadef.UpdateWorkPackageQuantityPayload

#     async def _process(self, agg, stm, payload):
#         """Update work package quantity in estimator"""
#         await agg.update_work_package_quantity(
#             work_package_id=payload.work_package_id,
#             quantity=payload.quantity
#         )
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class RemoveWorkPackageFromEstimator(Command):
#     """Remove Work Package From Estimator - Removes a Work Package from the current estimator draft"""

#     class Meta:
#         key = "remove-work-package-from-estimator"
#         resources = ("project",)
#         tags = ["project", "work-package"]
#         auth_required = True
#         description = "Remove work package from estimator"

#     Data = datadef.RemoveWorkPackagePayload

#     async def _process(self, agg, stm, payload):
#         """Remove work package from estimator"""
#         await agg.remove_work_package_from_estimator(payload.work_package_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UpdateProjectDetails(Command):
#     """Update Project Details - Updates mutable details of an existing project"""

#     class Meta:
#         key = "update-detail"
#         resources = ("project",)
#         tags = ["project", "update"]
#         auth_required = True
#         description = "Update project details"

#     Data = datadef.UpdateProjectPayload

#     async def _process(self, agg, stm, payload):
#         """Update project details"""
#         update_data = payload.dict(exclude_none=True)
#         await agg.update_project_details(update_data)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


class AddProjectMember(Command):
    """Add Project Member - Assigns a user (member) to a specific project with a defined role"""

    class Meta:
        key = "add-member"
        resources = ("project",)
        tags = ["project", "member"]
        auth_required = True
        description = "Add member to project"

    Data = datadef.AddProjectMemberPayload

    async def _process(self, agg, stm, payload):
        """Add member to project"""
        await agg.add_project_member(
            member_id=payload.member_id,
            role=payload.role
        )
        # Get the updated project data
        project = await stm.fetch("project", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(project), _type="project-response")


# class AssignTeamToProject(Command):
#     """Assign Team to Project - Assigns an existing team to a specific project"""

#     class Meta:
#         key = "add-team"
#         resources = ("project",)
#         tags = ["project", "team"]
#         auth_required = True
#         description = "Assign team to project"

#     Data = datadef.AddProjectMemberPayload  # Reusing member payload for team

#     async def _process(self, agg, stm, payload):
#         """Assign team to project"""
#         await agg.assign_team_to_project(
#             team_id=payload.member_id,  # Using member_id field for team_id
#             role=payload.role
#         )
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UpdateProjectMemberRole(Command):
#     """Update Project Member Role - Updates the role of an existing member within a project"""

#     class Meta:
#         key = "update-member-role"
#         resources = ("project",)
#         tags = ["project", "member"]
#         auth_required = True
#         description = "Update project member role"

#     Data = datadef.UpdateProjectMemberRolePayload

#     async def _process(self, agg, stm, payload):
#         """Update project member role"""
#         await agg.update_project_member_role(
#             member_id=payload.member_id,
#             role=payload.role
#         )
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class RemoveProjectMember(Command):
#     """Remove Project Member - Removes a member from a project"""

#     class Meta:
#         key = "remove-member-from-project"
#         resources = ("project",)
#         tags = ["project", "member"]
#         auth_required = True
#         description = "Remove member from project"

#     Data = datadef.RemoveProjectMemberPayload

#     async def _process(self, agg, stm, payload):
#         """Remove member from project"""
#         await agg.remove_project_member(payload.member_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class DefineProjectMilestone(Command):
#     """Define Project Milestone - Adds a new milestone to a project"""

#     class Meta:
#         key = "create-milestone"
#         resources = ("project",)
#         tags = ["project", "milestone"]
#         auth_required = True
#         description = "Create project milestone"

#     Data = datadef.CreateMilestonePayload

#     async def _process(self, agg, stm, payload):
#         """Create project milestone"""
#         await agg.create_project_milestone(
#             name=payload.name,
#             due_date=payload.due_date,
#             description=payload.description
#         )
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UpdateProjectMilestone(Command):
#     """Update Project Milestone - Updates an existing milestone's details"""

#     class Meta:
#         key = "update-milestone"
#         resources = ("project",)
#         tags = ["project", "milestone"]
#         auth_required = True
#         description = "Update project milestone"

#     Data = datadef.UpdateMilestonePayload

#     async def _process(self, agg, stm, payload):
#         """Update project milestone"""
#         update_data = payload.dict(exclude_none=True)
#         await agg.update_project_milestone(payload.milestone_id, update_data)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class MarkProjectMilestoneCompleted(Command):
#     """Mark Project Milestone Completed - Marks a milestone as completed"""

#     class Meta:
#         key = "complete-milestone"
#         resources = ("project",)
#         tags = ["project", "milestone"]
#         auth_required = True
#         description = "Mark milestone as completed"

#     Data = datadef.CompleteMilestonePayload

#     async def _process(self, agg, stm, payload):
#         """Mark milestone as completed"""
#         await agg.complete_project_milestone(payload.milestone_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UnmarkProjectMilestone(Command):
#     """Unmark Project Milestone - Unmarks a milestone as completed"""

#     class Meta:
#         key = "uncomplete-milestone"
#         resources = ("project",)
#         tags = ["project", "milestone"]
#         auth_required = True
#         description = "Unmark milestone as completed"

#     Data = datadef.CompleteMilestonePayload

#     async def _process(self, agg, stm, payload):
#         """Unmark milestone as completed"""
#         await agg.uncomplete_project_milestone(payload.milestone_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class DeleteProjectMilestone(Command):
#     """Delete Project Milestone - Deletes a milestone from a project"""

#     class Meta:
#         key = "delete-milestone"
#         resources = ("project",)
#         tags = ["project", "milestone"]
#         auth_required = True
#         description = "Delete project milestone"

#     Data = datadef.DeleteMilestonePayload

#     async def _process(self, agg, stm, payload):
#         """Delete project milestone"""
#         await agg.delete_project_milestone(payload.milestone_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


# class UploadProjectResource(Command):
#     """Upload Project Resource - Upload new resource into current project"""

#     class Meta:
#         key = "upload-resource"
#         resources = ("project",)
#         tags = ["project", "resource"]
#         auth_required = True
#         description = "Upload resource to project"

#     Data = datadef.UploadProjectResourcePayload

#     async def _process(self, agg, stm, payload):
#         """Upload resource to project"""
#         media_id = await agg.upload_project_resource(
#             file=payload.file,
#             type=payload.type,
#             description=payload.description
#         )
#         yield agg.create_response({"media_id": media_id}, _type="resource-upload")


# class DeleteProjectResource(Command):
#     """Delete Project Resource - Delete a resource in current project"""

#     class Meta:
#         key = "delete-resource"
#         resources = ("project",)
#         tags = ["project", "resource"]
#         auth_required = True
#         description = "Delete project resource"

#     Data = datadef.DeleteProjectResourcePayload

#     async def _process(self, agg, stm, payload):
#         """Delete project resource"""
#         await agg.delete_project_resource(payload.resource_id)
#         # Get the updated project data
#         project = await stm.fetch("project", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(project), _type="project-response")


class CreateProjectCategory(Command):
    """Create Project Category - Creates a new project category"""

    class Meta:
        key = "create-project-category"
        resources = ("project",)
        tags = ["project", "category"]
        auth_required = True
        description = "Create a new project category"
        new_resource = True

    Data = datadef.CreateProjectCategoryPayload

    async def _process(self, agg, stm, payload):
        """Create project category"""
        result = await agg.create_project_category(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-category-response")


# ---------- Ticket Context ----------

class CreateInquiry(Command):
    """Create Inquiry - Creates a new inquiry (ticket not tied to project)"""

    class Meta:
        key = "create-inquiry"
        resources = ("ticket",)
        tags = ["ticket", "inquiry"]
        auth_required = True
        description = "Create a new inquiry"
        new_resource = True

    Data = datadef.CreateInquiryPayload

    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        user_id = context.user_id
        payload = payload.set(creator=user_id)
        result = await agg.create_inquiry(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class CreateTicket(Command):
    """Create Ticket - Creates a new ticket tied to a project"""

    class Meta:
        key = "create-ticket"
        resources = ("ticket",)
        tags = ["ticket"]
        auth_required = True
        description = "Create a new ticket in project"
        new_resource = True

    Data = datadef.CreateProjectTicketPayload

    async def _process(self, agg, stm, payload):
        """Create a new ticket in project"""
        context = agg.get_context()
        user_id = context.user_id

        result = await agg.create_ticket(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class UpdateInquiryInfo(Command):
    """Update Inquiry Info - Updates inquiry information"""

    class Meta:
        key = "update-inquiry"
        resources = ("ticket",)
        tags = ["inquiry", "update"]
        auth_required = True
        description = "Update inquiry information"

    Data = datadef.UpdateInquiryPayload

    async def _process(self, agg, stm, payload):
        ticket = await agg.update_ticket_info(payload)
        yield agg.create_response(ticket, _type="ticket-response")


class UpdateTicketInfo(Command):
    """Update Ticket Info - Updates ticket information"""

    class Meta:
        key = "update-ticket"
        resources = ("ticket",)
        tags = ["ticket", "update"]
        auth_required = True
        description = "Update ticket information"

    Data = datadef.UpdateTicketPayload

    async def _process(self, agg, stm, payload):
        ticket = await agg.update_ticket_info(payload)
        yield agg.create_response(ticket, _type="ticket-response")


class CloseTicket(Command):
    """Close Ticket - Closes a specific ticket"""

    class Meta:
        key = "close-ticket"
        resources = ("ticket",)
        tags = ["ticket"]
        auth_required = True
        description = "Close a specific ticket"

    async def _process(self, agg, stm, payload):
        """Close ticket"""
        ticket = await agg.close_ticket()
        yield agg.create_response(ticket, _type="ticket-response")


class ReopenTicket(Command):
    """Reopen Ticket - Reopens a specific ticket"""

    class Meta:
        key = "reopen-ticket"
        resources = ("ticket",)
        tags = ["ticket"]
        auth_required = True
        description = "Reopen a specific ticket"

    async def _process(self, agg, stm, payload):
        """Reopen ticket"""
        await agg.reopen_ticket()
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


class ChangeTicketStatus(Command):
    """Change Ticket Status - Changes ticket status using workflow"""

    class Meta:
        key = "change-ticket-status"
        resources = ("ticket",)
        tags = ["ticket", "workflow"]
        auth_required = True
        description = "Change ticket status using workflow"

    Data = datadef.ChangeTicketStatusPayload

    async def _process(self, agg, stm, payload):
        """Change ticket status"""
        await agg.change_ticket_status(
            next_status=payload.next_status,
            note=payload.note
        )
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


class AssignMemberToTicket(Command):
    """Assign Member to Ticket - Assigns a member to ticket"""

    class Meta:
        key = "assign-member"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Assign member to ticket"

    Data = datadef.AssignTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Assign member to ticket"""
        await agg.assign_member_to_ticket(payload.member_id)
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


class RemoveMemberFromTicket(Command):
    """Remove Member from Ticket - Removes a member from ticket"""

    class Meta:
        key = "remove-member-from-ticket"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Remove member from ticket"

    Data = datadef.RemoveTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from ticket"""
        await agg.remove_member_from_ticket(payload.member_id)
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


class AddTicketComment(Command):
    """Add Comment to Ticket - Adds a comment to ticket"""

    class Meta:
        key = "add-ticket-comment"
        resources = ("ticket",)
        tags = ["ticket", "comment"]
        auth_required = True
        description = "Add comment to ticket"

    Data = datadef.AddTicketCommentPayload

    async def _process(self, agg, stm, payload):
        """Add comment to ticket"""
        await agg.add_ticket_comment(payload.comment_id)
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


class AddParticipantToTicket(Command):
    """Add Participant to Ticket - Adds a participant to ticket"""

    class Meta:
        key = "add-participant-to-ticket"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Add participant to ticket"

    Data = datadef.AddTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Add participant to ticket"""
        await agg.add_ticket_participant(payload.participant_id)


# ---------- Tag Context ----------
class CreateTag(Command):
    """Create Tag - Creates a new tag"""

    class Meta:
        key = "create-tag"
        resources = ("tag",)
        tags = ["tag"]
        auth_required = True
        description = "Create a new tag in project"
        new_resource = True

    Data = datadef.CreateTagPayload

    async def _process(self, agg, stm, payload):
        """Create tag"""
        result = await agg.create_tag(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="tag-response")


class CreateTicketType(Command):
    """Create Ticket Type - Creates a new ticket type"""

    class Meta:
        key = "create-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "reference"]
        auth_required = True
        description = "Create a new ticket type"
        new_resource = True

    Data = datadef.CreateTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Create ticket type"""
        result = await agg.create_ticket_type(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-type-response")


class AddTicketTag(Command):
    """Add Tag to Ticket - Adds a tag to ticket"""

    class Meta:
        key = "add-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Add tag to ticket"

    Data = datadef.AddTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Add tag to ticket"""
        await agg.add_ticket_tag(payload.tag_id)


class RemoveTicketTag(Command):
    """Remove Tag from Ticket - Removes a tag from ticket"""

    class Meta:
        key = "remove-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Remove tag from ticket"

    Data = datadef.RemoveTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Remove tag from ticket"""
        await agg.remove_ticket_tag(payload.tag_id)
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


# ---------- Work Package Context ----------
class CreateWorkPackage(Command):
    """Create Work Package - For internal/admin use — adds new reusable WP"""

    class Meta:
        key = "create-work-package"
        resources = ("work-package",)
        tags = ["work-package", "create"]
        new_resource = True
        auth_required = True
        description = "Create new work package"

    Data = datadef.CreateWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Create new work package"""
        result = await agg.create_work_package(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="work-package-response")


class CreateWorkItemDeliverable(Command):
    """Create Work Item Deliverable - Creates a new deliverable for a work item"""

    class Meta:
        key = "create-work-item-deliverable"
        resources = ("work-item",)
        tags = ["work-item", "deliverable", "create"]
        new_resource = True
        auth_required = True
        description = "Create new work package deliverable"

    Data = datadef.CreateWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Create new work item deliverable"""
        result = await agg.create_work_item_deliverable(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="work-item-deliverable-response")


class InvalidateWorkItemDeliverable(Command):
    """Invalidate Work Item Deliverable - Invalidate a work item deliverable"""

    class Meta:
        key = "invalidate-work-item-deliverable"
        resources = ("work-item",)
        tags = ["work-item", "deliverable", "invalidate"]
        auth_required = True
        description = "Invalidate work package deliverable"

    Data = datadef.InvalidateWorkPackageDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Invalidate work package deliverable"""
        await agg.invalidate_work_package_deliverable(data=payload)


class UpdateWorkPackage(Command):
    """Update Work Package - Admin can update a reusable WP"""

    class Meta:
        key = "update-work-package"
        resources = ("work-package",)
        tags = ["work-package", "update"]
        auth_required = True
        description = "Update work package"

    Data = datadef.UpdateWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Update work package"""
        update_data = payload.dict(exclude_none=True)
        result = await agg.update_work_package(update_data)
        yield agg.create_response(serialize_mapping(result), _type="work-package-response")


class InvalidateWorkPackage(Command):
    """Invalidate Work Package - Invalidate a work package"""

    class Meta:
        key = "invalidate-work-package"
        resources = ('work-package', )
        tags = ['work-package', 'invalidate']
        auth_required = True
        description = "Invalidate work package"

    async def _process(self, aggregate, stm, payload):
        await aggregate.invalidate_work_package()


# ---------- Work Item Context ----------
class CreateWorkItem(Command):
    """Create Work Item - Creates a new work item"""

    class Meta:
        key = "create-work-item"
        resources = ("work-item",)
        tags = ["work-item", "create"]
        new_resource = True

    Data = datadef.CreateWorkItemPayload

    async def _process(self, agg, stm, payload):
        """Create new work item"""
        result = await agg.create_work_item(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="work-item-response")


class CreateWorkItemType(Command):
    """Create Work Item Type - Creates a new work item type"""

    class Meta:
        key = "create-work-item-type"
        resources = ("work-item",)
        tags = ["work-item", "type", "reference"]
        new_resource = True

    Data = datadef.CreateWorkItemTypePayload

    async def _process(self, agg, stm, payload):
        """Create new work item type"""
        result = await agg.create_work_item_type(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="work-item-type-response")


class AddWorkItemToWorkPackage(Command):
    """Add Work Item to Work Package - Adds a work item to a work package"""

    class Meta:
        key = "add-work-item-to-work-package"
        resources = ("work-package",)
        tags = ["work-package", "work-item", "add"]

    Data = datadef.AddWorkItemToWorkPackagePayload

    async def _process(self, agg, stm, payload):
        await agg.add_work_item_to_work_package(payload.work_item_id)


# ---------- Notification Context ----------
class MarkNotificationAsRead(Command):
    """Mark Notification As Read - Update is_read status of a specific notification to true"""

    class Meta:
        key = "mark-notfication-as-read"
        resources = ("notification",)
        tags = ["notification"]
        auth_required = True
        description = "Mark notification as read"

    Data = datadef.MarkNotificationAsReadPayload

    async def _process(self, agg, stm, payload):
        """Mark notification as read"""


class MarkAllNotificationsAsRead(Command):
    """Mark All Notification As Read - Updates the is_read status of all notifications for the authenticated user to true"""

    class Meta:
        key = "mark-all-notfication-as-read"
        resources = ("notification",)
        tags = ["notification"]
        auth_required = True
        description = "Mark all notifications as read"

    Data = datadef.MarkAllNotificationsAsReadPayload

    async def _process(self, agg, stm, payload):
        """Mark all notifications as read"""


# ---------- Integration Context ----------
class UnifiedSync(Command):
    """Sync Client Portal items to External System - Unified sync command to sync data of client portal system to other external resource"""

    class Meta:
        key = "unified-sync"
        resources = ("integration",)
        tags = ["integration", "sync"]
        auth_required = True
        description = "Unified sync command"

    Data = datadef.UnifiedSyncPayload

    async def _process(self, agg, stm, payload):
        """Unified sync command"""
