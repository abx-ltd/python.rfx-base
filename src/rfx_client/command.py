from fluvius.data import serialize_mapping

from .domain import CPOPortalDomain
from . import datadef, config
from fluvius.data import UUID_TYPE, UUID_GENR

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
        result = await agg.create_project_estimator(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-response")


class CreateProject(Command):
    """Create Project - Creates a new project - this is a conversion from estimator"""

    class Meta:
        key = "create-project"
        resources = ("project",)
        tags = ["project"]
        auth_required = True
        description = "Create a new project directly"

    Data = datadef.CreateProjectPayload

    async def _process(self, agg, stm, payload):
        """Create a new project directly"""
        result = await agg.create_project(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-response")


class DeleteProject(Command):
    """Delete Project - Deletes a project"""

    class Meta:
        key = "delete-project"
        resources = ("project",)
        tags = ["project", "delete"]
        auth_required = True
        description = "Delete a project"

    async def _process(self, agg, stm, payload):
        """Delete a project"""
        await agg.delete_project()


class CreateProjectBDMContact(Command):
    """Create Project BDM Contact - Creates a new BDM contact for a project"""

    class Meta:
        key = "create-project-bdm-contact"
        resources = ("project",)
        tags = ["project", "bdm", "contact"]
        auth_required = True
        description = "Create a new BDM contact for a project"

    Data = datadef.CreateProjectBDMContactPayload

    async def _process(self, agg, stm, payload):
        """Create a new BDM contact for a project"""
        result = await agg.create_project_bdm_contact(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-bdm-contact-response")


class UpdateProjectBDMContact(Command):
    """Update Project BDM Contact - Updates a project BDM contact"""

    class Meta:
        key = "update-project-bdm-contact"
        resources = ("project",)
        tags = ["project", "bdm", "contact"]
        auth_required = True
        description = "Update a project BDM contact"

    Data = datadef.UpdateProjectBDMContactPayload

    async def _process(self, agg, stm, payload):
        """Update a project BDM contact"""
        await agg.update_project_bdm_contact(data=payload)


class DeleteProjectBDMContact(Command):
    """Delete Project BDM Contact - Deletes a project BDM contact"""

    class Meta:
        key = "delete-project-bdm-contact"
        resources = ("project",)
        tags = ["project", "bdm", "contact"]
        auth_required = True
        description = "Delete a project BDM contact"

    Data = datadef.DeleteProjectBDMContactPayload

    async def _process(self, agg, stm, payload):
        """Delete a project BDM contact"""
        await agg.delete_project_bdm_contact(data=payload)


class CreatePromotion(Command):
    """Create Promotion Code - Creates a new promotion code"""

    class Meta:
        key = "create-promotion"
        resources = ("promotion",)
        tags = ["promotion", "code"]
        auth_required = True
        description = "Create a new promotion code"
        new_resource = True

    Data = datadef.CreatePromotionPayload

    async def _process(self, agg, stm, payload):
        """Create a new promotion code"""
        result = await agg.create_promotion(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="promotion-response")


class UpdatePromotion(Command):
    """Update Promotion Code - Updates a promotion code"""

    class Meta:
        key = "update-promotion"
        resources = ("promotion",)
        tags = ["promotion", "code"]
        auth_required = True
        description = "Update a promotion code"

    Data = datadef.UpdatePromotionPayload

    async def _process(self, agg, stm, payload):
        """Update a promotion code"""
        await agg.update_promotion(data=payload)


class ApplyPromotion(Command):
    """Apply Promotion - Applies a promotion code to a project"""

    class Meta:
        key = "apply-promotion"
        resources = ("project",)
        tags = ["project", "promotion"]
        auth_required = True
        description = "Apply a promotion code to a project"

    Data = datadef.ApplyPromotionPayload

    async def _process(self, agg, stm, payload):
        """Apply a promotion code to a project"""
        await agg.apply_promotion(data=payload)


class AddWorkPackageToProject(Command):
    """Add Work Package to Project - Adds a specific Work Package to the project"""

    class Meta:
        key = "add-work-package-to-project"
        resources = ("project",)
        tags = ["project", "work-package"]
        auth_required = True
        description = "Add work package to current estimator draft"

    Data = datadef.AddWorkPackageToProjectPayload

    async def _process(self, agg, stm, payload):
        """Add work package to estimator draft"""
        return await agg.add_work_package_to_estimator(data=payload)


class RemoveWorkPackageFromProject(Command):
    """Remove Work Package from Project - Removes a specific Work Package from the project"""

    class Meta:
        key = "remove-work-package-from-project"
        resources = ("project",)
        tags = ["project", "work-package"]
        auth_required = True
        description = "Remove work package from project"

    Data = datadef.RemoveWorkPackageFromProjectPayload

    async def _process(self, agg, stm, payload):
        """Remove work package from project"""
        return await agg.remove_work_package_from_estimator(data=payload)


class AddTicketToProject(Command):
    class Meta:
        key = "add-ticket-to-project"
        resources = ("project",)
        tags = ["project", "ticket"]
        auth_required = True
        description = "Add ticket to project"
        new_resource = True
        internal = True

    Data = datadef.AddTicketToProjectPayload

    async def _process(self, agg, sta, payload):
        result = await agg.add_ticket_to_project(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-response")


class CreateProjectTicker(Command):
    class Meta:
        key = "create-project-ticket"
        resources = ("project",)
        tags = ["project", "ticket"]
        auth_required = True
        description = "Create project ticket"

    Data = datadef.CreateProjectTicketPayload

    async def _process(self, agg, sta, payload):
        aggroot = agg.get_aggroot()
        project_id = aggroot.identifier
        ticket_id = UUID_GENR()
        yield agg.create_message(
            "discussion-message",
            data={
                "command": "create-ticket",
                "ticket_id": str(ticket_id),
                "payload": serialize_mapping(payload),
                "context": {}  # Added missing context field
            }
        )
        yield agg.create_message(
            "project-message",
            data={
                "command": "add-ticket-to-project",
                "project_id": str(project_id),
                "payload": {
                    "ticket_id": ticket_id
                }
            }
        )


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


class RemoveProjectMember(Command):
    """Remove Project Member - Removes a member from a project"""

    class Meta:
        key = "remove-member"
        resources = ("project",)
        tags = ["project", "member"]
        auth_required = True
        description = "Remove member from project"

    Data = datadef.RemoveProjectMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from project"""
        await agg.remove_project_member(member_id=payload.member_id)


class CreateProjectMilestone(Command):
    """Create Project Milestone - Creates a new milestone for a project"""

    class Meta:
        key = "create-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Create a new milestone for a project"

    Data = datadef.CreateProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Create a new milestone for a project"""
        result = await agg.create_project_milestone(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-milestone-response")


class UpdateProjectMilestone(Command):
    """Update Project Milestone - Updates a project milestone"""

    class Meta:
        key = "update-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Update project milestone"

    Data = datadef.UpdateProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Update project milestone"""
        await agg.update_project_milestone(data=payload)


class DeleteProjectMilestone(Command):
    """Delete Project Milestone - Deletes a project milestone"""

    class Meta:
        key = "delete-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Delete project milestone"
        batch_command = True

    Data = datadef.DeleteProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Delete project milestone"""
        await agg.delete_project_milestone(data=payload)


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


class UpdateProjectCategory(Command):
    """Update Project Category - Updates a project category"""

    class Meta:
        key = "update-project-category"
        resources = ("project",)
        tags = ["project", "category"]
        auth_required = True
        description = "Update project category"
        new_resource = True

    Data = datadef.UpdateProjectCategoryPayload

    async def _process(self, agg, stm, payload):
        """Update project category"""
        await agg.update_project_category(data=payload)


class DeleteProjectCategory(Command):
    """Delete Project Category - Deletes a project category"""

    class Meta:
        key = "delete-project-category"
        resources = ("project",)
        tags = ["project", "category"]
        auth_required = True
        description = "Delete project category"
        new_resource = True

    Data = datadef.DeleteProjectCategoryPayload

    async def _process(self, agg, stm, payload):
        """Delete project category"""
        await agg.delete_project_category(data=payload)


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


class DeleteWorkPackage(Command):
    """Invalidate Work Package - Invalidate a work package"""

    class Meta:
        key = "delete-work-package"
        resources = ('work-package', )
        tags = ['work-package', 'delete']
        auth_required = True
        description = "Delete work package"

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


class UpdateWorkItem(Command):
    """Update Work Item - Updates a work item"""

    class Meta:
        key = "update-work-item"
        resources = ("work-item",)
        tags = ["work-item", "update"]
        auth_required = True
        description = "Update work item"

    Data = datadef.UpdateWorkItemPayload

    async def _process(self, agg, stm, payload):
        """Update work item"""
        await agg.update_work_item(data=payload)


class DeleteWorkItem(Command):
    """Delete Work Item - Deletes a work item"""

    class Meta:
        key = "delete-work-item"
        resources = ("work-item",)
        tags = ["work-item", "delete"]
        auth_required = True
        description = "Delete work item"

    async def _process(self, agg, stm, payload):
        """Delete work item"""
        await agg.invalidate_work_item(data=payload)


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


# class UpdateWorkItemType(Command):
#     """Update Work Item Type - Updates a work item type"""

#     class Meta:
#         key = "update-work-item-type"
#         resources = ("work-item",)
#         tags = ["work-item", "type", "update"]
#         auth_required = True
#         description = "Update work item type"

#     Data = datadef.UpdateWorkItemTypePayload

#     async def _process(self, agg, stm, payload):
#         """Update work item type"""
#         await agg.update_work_item_type(data=payload)


# class DeleteWorkItemType(Command):
#     """Delete Work Item Type - Deletes a work item type"""

#     class Meta:
#         key = "delete-work-item-type"
#         resources = ("work-item",)
#         tags = ["work-item", "type", "delete"]
#         auth_required = True
#         description = "Delete work item type"

#     async def _process(self, agg, stm, payload):
#         """Delete work item type"""
#         await agg.invalidate_work_item_type(data=payload)


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


class UpdateWorkItemDeliverable(Command):

    class Meta:
        key = "update-work-item-deliverable"
        resources = ("work-item",)
        tags = ["work-item", "deliverable", "update"]
        auth_required = True
        description = "Update work item deliverable"

    Data = datadef.UpdateWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Update work item deliverable"""
        await agg.update_work_item_deliverable(data=payload)


class DeleteWorkItemDeliverable(Command):
    """Invalidate Work Item Deliverable - Invalidate a work item deliverable"""

    class Meta:
        key = "delete-work-item-deliverable"
        resources = ("work-item",)
        tags = ["work-item", "deliverable", "delete"]
        auth_required = True
        description = "Delete work package deliverable"

    Data = datadef.DeleteWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Invalidate work package deliverable"""
        await agg.invalidate_work_item_deliverable(data=payload)


class AddWorkItemToWorkPackage(Command):
    """Add Work Item to Work Package - Adds a work item to a work package"""

    class Meta:
        key = "add-work-item-to-work-package"
        resources = ("work-package",)
        tags = ["work-package", "work-item", "add"]

    Data = datadef.AddWorkItemToWorkPackagePayload

    async def _process(self, agg, stm, payload):
        await agg.add_work_item_to_work_package(payload.work_item_id)


class RemoveWorkItemFromWorkPackage(Command):
    """Remove Work Item from Work Package - Removes a work item from a work package"""

    class Meta:
        key = "remove-work-item-from-work-package"
        resources = ("work-package",)
        tags = ["work-package", "work-item", "remove"]
        auth_required = True
        description = "Remove work item from work package"

    Data = datadef.RemoveWorkItemFromWorkPackagePayload

    async def _process(self, agg, stm, payload):
        await agg.remove_work_item_from_work_package(payload.work_item_id)


# # ---------- Notification Context ----------
# class MarkNotificationAsRead(Command):
#     """Mark Notification As Read - Update is_read status of a specific notification to true"""

#     class Meta:
#         key = "mark-notfication-as-read"
#         resources = ("notification",)
#         tags = ["notification"]
#         auth_required = True
#         description = "Mark notification as read"

#     Data = datadef.MarkNotificationAsReadPayload

#     async def _process(self, agg, stm, payload):
#         """Mark notification as read"""


# class MarkAllNotificationsAsRead(Command):
#     """Mark All Notification As Read - Updates the is_read status of all notifications for the authenticated user to true"""

#     class Meta:
#         key = "mark-all-notfication-as-read"
#         resources = ("notification",)
#         tags = ["notification"]
#         auth_required = True
#         description = "Mark all notifications as read"

#     Data = datadef.MarkAllNotificationsAsReadPayload

#     async def _process(self, agg, stm, payload):
#         """Mark all notifications as read"""


# # ---------- Integration Context ----------
# class UnifiedSync(Command):
#     """Sync Client Portal items to External System - Unified sync command to sync data of client portal system to other external resource"""

#     class Meta:
#         key = "unified-sync"
#         resources = ("integration",)
#         tags = ["integration", "sync"]
#         auth_required = True
#         description = "Unified sync command"

#     Data = datadef.UnifiedSyncPayload

#     async def _process(self, agg, stm, payload):
#         """Unified sync command"""
