from email import message
from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXClientDomain
from . import datadef, config
from .types import ActivityAction
from fluvius.data import UUID_TYPE, UUID_GENR, logger
from .helper import get_project_member_user_ids

processor = RFXClientDomain.command_processor
Command = RFXClientDomain.Command


# ---------- Estimator (Project Context)----------

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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        yield agg.create_activity(
            logroot=AggregateRoot(
                resource="project",
                identifier=result._id,
                domain_sid=agg.get_aggroot().domain_sid,
                domain_iid=agg.get_aggroot().domain_iid,
            ),
            message=f"{profile.name__given} {profile.name__family} created an estimator {result.name}",
            msglabel="create-estimator",
            msgtype=ActivityType.USER_ACTION,
            data={
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(result), _type="project-response")


# ---------- Project (Project Context) ----------
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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a project {result.name}",
            msglabel="create-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": result.name,
                "status": result.status,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )


class UpdateProject(Command):
    """Update Project - Updates a project"""

    class Meta:
        key = "update-project"
        resources = ("project",)
        tags = ["project", "update"]
        auth_required = True
        description = "Update a project"

    Data = datadef.UpdateProjectPayload

    async def _process(self, agg, stm, payload):
        """Update a project"""
        await agg.update_project(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project {project.name}",
            msglabel="update-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": project.name,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        message_subject = "Project Updated"
        if project.status == "DRAFT":
            message_subject = "Estimator Updated"

        message_content = f"{profile.name__given} {profile.name__family} updated a project {project.name}"
        if project.status == "DRAFT":
            message_content = f"{profile.name__given} {profile.name__family} updated an estimator {project.name}"

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": message_subject,
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": message_content,
                    "content_type": "TEXT",
                },
                "context": {
                    "user_id": str(agg.get_context().user_id),
                    "profile_id": str(agg.get_context().profile_id),
                    "organization_id": str(agg.get_context().organization_id),
                    "realm": agg.get_context().realm,
                }
            }
        )


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a project {project.name}",
            msglabel="delete-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": project.name,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.delete_project()
        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Project Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a project {project.name}",
                    "content_type": "TEXT",
                },
                "context": {
                    "user_id": str(agg.get_context().user_id),
                    "profile_id": str(agg.get_context().profile_id),
                    "organization_id": str(agg.get_context().organization_id),
                    "realm": agg.get_context().realm,
                }
            }
        )


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} applied a promotion code {payload.promotion_code} to estimator {project.name}",
            msglabel="apply-promotion",
            msgtype=ActivityType.USER_ACTION,
            data={
                "promotion_code": payload.promotion_code,
                "applied_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Promotion Applied",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} applied a promotion code {payload.promotion_code}",
                    "content_type": "TEXT",
                },
                "context": {
                    "user_id": str(agg.get_context().user_id),
                    "profile_id": str(agg.get_context().profile_id),
                    "organization_id": str(agg.get_context().organization_id),
                    "realm": agg.get_context().realm,
                }
            }
        )

# ---------- Project BDM Contact (Still  in Project Context) ----------


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
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a BDM contact",
            msglabel="create-project-bdm-contact",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_bdm_contact_id": result._id,
                "message": result.message,
                "meeting_time": result.meeting_time,
                "status": result.status,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        yield agg.create_response(serialize_mapping(result), _type="project-bdm-contact-response")

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Created",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} created a BDM contact for project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a BDM contact",
            msglabel="update-project-bdm-contact",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_bdm_contact_id": payload.bdm_contact_id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a BDM contact of project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a BDM contact of project {project.name}",
            msglabel="delete-project-bdm-contact",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_bdm_contact_id": payload.bdm_contact_id,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        await agg.delete_project_bdm_contact(data=payload)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a BDM contact",
                    "content_type": "TEXT",
                },
            }
        )


# ---------- Promotion Context ----------
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


class RemovePromotion(Command):
    """Remove Promotion - Removes a promotion code"""

    class Meta:
        key = "remove-promotion"
        resources = ("promotion",)
        tags = ["promotion", "code"]
        auth_required = True
        description = "Remove a promotion code"

    async def _process(self, agg, stm, payload):
        """Remove a promotion code"""
        await agg.remove_promotion(data=payload)

# ---------- Project (Project Context) ----------


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        result = await agg.add_work_package_to_estimator(data=payload)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added",
            msglabel="add-work-package-to-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": result._id,
                "work_package_id": result.work_package_id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(result), _type="project-work-package-response")

        user_ids = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a work package",
                    "content_type": "TEXT",
                },
            }
        )


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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a work package",
            msglabel="remove-work-package-from-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "work_package_id": payload.work_package_id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.remove_work_package_from_estimator(data=payload)

        user_ids = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Removed",

                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed a work package",
                    "content_type": "TEXT",
                },
            }
        )


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

    async def _process(self, agg, stm, payload):

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.add_ticket_to_project(data=payload)
        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a ticket",
            msglabel="add-ticket-to-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": payload.ticket_id,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(result), _type="project-response")


class CreateProjectTicker(Command):
    class Meta:
        key = "create-project-ticket"
        resources = ("project",)
        tags = ["project", "ticket"]
        auth_required = True
        description = "Create project ticket"

    Data = datadef.CreateProjectTicketPayload

    async def _process(self, agg, stm, payload):
        aggroot = agg.get_aggroot()
        project_id = aggroot.identifier
        ticket_id = UUID_GENR()
        yield agg.create_message(
            "discussion-message",
            data={
                "command": "create-ticket",
                "ticket_id": str(ticket_id),
                "payload": serialize_mapping(payload),
                "context": {
                    "user_id": agg.get_context().user_id,
                    "profile_id": agg.get_context().profile_id,
                    "organization_id": agg.get_context().organization_id,
                    "realm": agg.get_context().realm,
                }
            }
        )
        yield agg.create_message(
            "project-message",
            data={
                "command": "add-ticket-to-project",
                "project_id": str(project_id),
                "payload": {
                    "ticket_id": ticket_id
                },
                "context": {
                    "user_id": agg.get_context().user_id,
                    "profile_id": agg.get_context().profile_id,
                    "organization_id": agg.get_context().organization_id,
                    "realm": agg.get_context().realm,
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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.add_project_member(
            member_id=payload.member_id,
            role=payload.role
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a member",
            msglabel="add-member-to-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": result.member_id,
                "role": result.role,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
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
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a member",
            msglabel="remove-member-from-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": payload.member_id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a milestone '{result.name}'",
            msglabel="create-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": result._id,
                "milestone_name": result.name,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_milestone = await stm.find_one(
            "project_milestone",
            {"_id": payload.milestone_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a milestone {project_milestone.name}",
            msglabel="update-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": payload.milestone_id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a milestone",
            msglabel="delete-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": payload.milestone_id,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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
        # yield agg.create_activity(
        #     logroot=agg.get_aggroot(),
        #     msglabel="work-item-created",
        #     message="Work Item Created",
        #     data={}
        # )


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


class UpdateWorkItemType(Command):
    """Update Work Item Type - Updates a work item type"""

    class Meta:
        key = "update-work-item-type"
        resources = ("work-item",)
        tags = ["work-item", "type", "update"]
        auth_required = True
        description = "Update work item type"
        new_resource = True

    Data = datadef.UpdateWorkItemTypePayload

    async def _process(self, agg, stm, payload):
        """Update work item type"""
        await agg.update_work_item_type(data=payload)


class DeleteWorkItemType(Command):
    """Delete Work Item Type - Deletes a work item type"""

    class Meta:
        key = "delete-work-item-type"
        resources = ("work-item",)
        tags = ["work-item", "type", "delete"]
        auth_required = True
        description = "Delete work item type"
        new_resource = True

    Data = datadef.DeleteWorkItemTypePayload

    async def _process(self, agg, stm, payload):
        """Delete work item type"""
        await agg.invalidate_work_item_type(data=payload)


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

# ---------- Project Work Item (Project Context) ----------


class UpdateProjectWorkItem(Command):
    """Update Project Work Item - Updates a project work item"""

    class Meta:
        key = "update-project-work-item"
        resources = ("project",)
        tags = ["project", "work-item", "update"]
        auth_required = True
        description = "Update project work item"

    Data = datadef.UpdateProjectWorkItemPayload

    async def _process(self, agg, stm, payload):
        """Update project work item"""
        await agg.update_project_work_item(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_item = await stm.find_one(
            "project_work_item",
            {"_id": payload.project_work_item_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project work item {project_work_item.name}",
            msglabel="update-project-work-item",
            msgtype=ActivityType.USER_ACTION,
            data={
                "work_item_id": project_work_item._id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )


class RemoveProjectWorkItem(Command):
    """Remove Project Work Item - Removes a project work item"""

    class Meta:
        key = "remove-project-work-item"
        resources = ("project",)
        tags = ["project", "work-item", "remove"]
        auth_required = True
        description = "Remove project work item"

    Data = datadef.RemoveProjectWorkItemPayload

    async def _process(self, agg, stm, payload):
        """Delete project work item"""
        await agg.invalidate_project_work_item(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_item = await stm.find_one(
            "project_work_item",
            {"_id": payload.project_work_item_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a project work item {project_work_item.name}",
            msglabel="remove-project-work-item",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_item_id": project_work_item._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )


# ---------- Project Work Package (Project Context) ----------

class UpdateProjectWorkPackage(Command):
    """Update Project Work Package - Updates a project work package"""

    class Meta:
        key = "update-project-work-package"
        resources = ("project",)
        tags = ["project", "work-package", "update"]
        auth_required = True
        description = "Update project work package"

    Data = datadef.UpdateProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Update project work package"""
        await agg.update_project_work_package(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_package = await stm.find_one(
            "project_work_package",
            {"_id": payload.project_work_package_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project work package {project_work_package.work_package_name}",
            msglabel="update-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )


# ---------- Project Work Package Work Item (Project Context) ----------

class AddNewWorkItemToProjectWorkPackage(Command):
    """Add New Work Item to Project Work Package - Adds a new work item to a project work package"""

    class Meta:
        key = "add-new-work-item-to-project-work-package"
        resources = ("project",)
        tags = ["project", "work-package", "work-item", "add"]

    Data = datadef.AddNewWorkItemToProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Add new work item to project work package"""
        await agg.add_new_work_item_to_project_work_package(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_package = await stm.find_one(
            "project_work_package",
            {"_id": payload.project_work_package_id}
        )

        project_work_item = await stm.find_one(
            "project_work_item",
            {"_id": payload.work_item_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a new work item {project_work_item.name} to a project work package {project_work_package.work_package_name}",
            msglabel="add-new-work-item-to-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "work_item_id": project_work_item._id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            }
        )


class RemoveWorkItemFromProjectWorkPackage(Command):

    class Meta:
        key = "remove-project-work-item-from-project-work-package"
        resources = ("project",)
        tags = ["project", "work-package", "work-item", "remove"]

    Data = datadef.RemoveProjectWorkItemFromProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Remove work item from project work package"""
        await agg.remove_project_work_item_from_project_work_package(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_item = await stm.find_one(
            "project_work_item",
            {"_id": payload.project_work_item_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a work item {project_work_item.name} from a project work package {project_work_package.work_package_name}",
            msglabel="remove-project-work-item-from-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )


# ---------- Project Work Item Deliverable (Project Context) ----------

class UpdateProjectWorkItemDeliverable(Command):
    """Update Project Work Item Deliverable - Updates a project work item deliverable"""

    class Meta:
        key = "update-project-work-item-deliverable"
        resources = ("project",)
        tags = ["project", "work-item", "deliverable", "update"]
        auth_required = True
        description = "Update project work item deliverable"

    Data = datadef.UpdateProjectWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Update project work item deliverable"""
        await agg.update_project_work_item_deliverable(data=payload)

        project_work_item_deliverable = await stm.find_one(
            "project_work_item_deliverable",
            {"_id": payload.project_work_item_deliverable_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Project work item deliverable updated: {project_work_item_deliverable.name}",
            msglabel="update-project-work-item-deliverable",
            msgtype=ActivityType.USER_ACTION,
            data={
                "updated_by": agg.get_context().user_id,
            }
        )


class DeleteProjectWorkItemDeliverable(Command):
    """Delete Project Work Item Deliverable - Deletes a project work item deliverable"""

    class Meta:
        key = "delete-project-work-item-deliverable"
        resources = ("project",)
        tags = ["project", "work-item", "deliverable", "delete"]
        auth_required = True
        description = "Delete project work item deliverable"

    Data = datadef.DeleteProjectWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Delete project work item deliverable"""
        await agg.invalidate_project_work_item_deliverable(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a project work item deliverable {project_work_item_deliverable.name}",
            msglabel="delete-project-work-item-deliverable",
            msgtype=ActivityType.USER_ACTION,
            data={
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            }
        )


class CreditUsageSummary(Command):
    """Credit Usage Summary - Get credit usage summary"""

    class Meta:
        key = "credit-usage-summary"
        resources = ("project",)
        tags = ["project", "credit", "usage", "summary"]
        auth_required = True
        description = "Get credit usage summary"
        new_resource = True

    Data = datadef.CreditUsageSummaryPayload

    async def _process(self, agg, stm, payload):
        """Get credit usage summary"""

        summary = await stm.get_credit_usage_query(
            organization_id=payload.organization_id,
        )

        yield agg.create_response({"data": [serialize_mapping(item) for item in summary]}, _type="credit-usage-summary-response")
