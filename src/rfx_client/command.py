from email import message
from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXClientDomain
from . import datadef, config
from .types import ActivityAction
from fluvius.data import UUID_TYPE, UUID_GENR, logger
from .helper import get_project_member_user_ids
from .integration import call_linear_api, get_linear_status_id, get_linear_user_id, get_linear_label_id
import datetime

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
        policy_required = True

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
        policy_required = True

    Data = datadef.CreateProjectPayload

    async def _process(self, agg, stm, payload):
        """Create a new project directly"""
        new_project = await agg.create_project(data=payload)
        yield agg.create_response(serialize_mapping(new_project), _type="project-response")

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a project {new_project.name}",
            msglabel="create-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": new_project.name,
                "status": new_project.status,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        
        if payload.sync_linear:
            yield agg.create_message(
                "create-linear-message",
                data={
                "command": "create-project-integration",
                "project": serialize_mapping(new_project),
                "project_id": str(agg.get_aggroot().identifier),
                "payload": {
                    "provider": "linear",
                    "external_id": str(agg.get_aggroot().identifier),
                },
                "context": {
                    "user_id": agg.get_context().user_id,
                    "profile_id": agg.get_context().profile_id,
                    "organization_id": agg.get_context().organization_id,
                    "realm": agg.get_context().realm,
                }
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
        policy_required = True

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
        if payload.sync_linear:
            yield agg.create_message(
                    "update-linear-message",
                    data={
                    "command": "update-project-integration",
                    "project": serialize_mapping(project),
                    "project_id": str(agg.get_aggroot().identifier),
                    "payload": {
                        "provider": "linear",
                        "external_id": str(agg.get_aggroot().identifier),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
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
        policy_required = True

    Data = datadef.DeleteProjectPayload

    async def _process(self, agg, stm, payload):
        """Delete a project"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        # if payload.sync_linear:
        #     await agg.delete_linear_project()

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
        
        if payload.sync_linear:
            yield agg.create_message(
                    "remove-linear-message",
                    data={
                    "command": "remove-project-integration",
                    "project": serialize_mapping(project),
                    # "project_id": str(agg.get_aggroot().identifier),
                    
                    "payload": {
                        "provider": "linear",
                        "external_id": str(agg.get_aggroot().identifier),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )
        await agg.delete_project()




class ApplyPromotion(Command):
    """Apply Promotion - Applies a promotion code to a project"""

    class Meta:
        key = "apply-promotion"
        resources = ("project",)
        tags = ["project", "promotion"]
        auth_required = True
        description = "Apply a promotion code to a project"
        policy_required = True

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
        policy_required = True

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
        policy_required = True

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
        policy_required = True

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = True

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

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        if project.status == "DRAFT":
            project_name = f"estimator {project.name}"
        else:
            project_name = f"project {project.name}"

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a work package to {project_name}",
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
        policy_required = True

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

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        if project.status == "DRAFT":
            project_name = f"estimator {project.name}"
        else:
            project_name = f"project {project.name}"

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Removed",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed a work package from {project_name}",
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
        policy_required = False

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


class CreateProjectTicket(Command):
    class Meta:
        key = "create-project-ticket"
        resources = ("project",)
        tags = ["project", "ticket"]
        auth_required = True
        description = "Create project ticket"
        policy_required = True

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
                "project_id": str(project_id),
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

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Ticket Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a ticket to project {project.name}",
                    "content_type": "TEXT",
                },
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
        policy_required = True

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

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        member = await stm.get_profile(payload.member_id)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added {member.name__given} {member.name__family} to project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )
class UpdateProjectMember(Command):
    """Update Project Member - Updates a member's role in a project"""

    class Meta:
        key = "update-member"
        resources = ("project",)
        tags = ["project", "member"]
        auth_required = True
        description = "Update member's role in project"
        policy_required = True

    Data = datadef.UpdateProjectMemberPayload

    async def _process(self, agg, stm, payload):
        """Update member's role in project"""
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a member's role",
            msglabel="update-project-member",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": payload.member_id,
                "role": payload.role,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.update_project_member(member_id=payload.member_id, role=payload.role)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Role Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated {member.name__given} {member.name__family}'s role in project {project.name}",
                    "content_type": "TEXT",
                },
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
        policy_required = True

    Data = datadef.RemoveProjectMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from project"""
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        member = await stm.get_profile(payload.member_id)

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

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Removed",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed {member.name__given} {member.name__family} from project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


class CreateProjectMilestone(Command):
    """Create Project Milestone - Creates a new milestone for a project"""

    class Meta:
        key = "create-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Create a new milestone for a project"
        policy_required = True

    Data = datadef.CreateProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Create a new milestone for a project"""
        result = await agg.create_project_milestone(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

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

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Created",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} created a milestone '{result.name}' for project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )
        
        if payload.sync_linear:
            yield agg.create_message(
                "create-milestone-message",
                data={
                    "command": "create-project-milestone-integration",
                    "milestone": serialize_mapping(result),
                    "project_id": str(agg.get_aggroot().identifier),
                    "payload": {
                        "provider": "linear",
                        "external_id": str(result._id),
                        "milestone_id": str(result._id),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )


class UpdateProjectMilestone(Command):
    """Update Project Milestone - Updates a project milestone"""

    class Meta:
        key = "update-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Update project milestone"
        policy_required = True

    Data = datadef.UpdateProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Update project milestone"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_milestone = await stm.find_one(
            "project-milestone",
            where={"_id": payload.milestone_id}
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

        result = await agg.update_project_milestone(data=payload)
        

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a milestone {project_milestone.name} in project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )
        
        if payload.sync_linear:
            yield agg.create_message(
                "update-milestone-message",
                data={
                    "command": "update-project-milestone-integration",
                    "milestone": serialize_mapping(result),
                    "project_id": str(agg.get_aggroot().identifier),
                    "payload": {
                        "provider": "linear",
                        "external_id": str(result._id),
                        "milestone_id": str(result._id),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )


class DeleteProjectMilestone(Command):
    """Delete Project Milestone - Deletes a project milestone"""

    class Meta:
        key = "delete-project-milestone"
        resources = ("project",)
        tags = ["project", "milestone"]
        auth_required = True
        description = "Delete project milestone"
        policy_required = True

    Data = datadef.DeleteProjectMilestonePayload

    async def _process(self, agg, stm, payload):
        """Delete project milestone"""
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_milestone = await stm.find_one(
            "project-milestone",
            where={"_id": payload.milestone_id}
        )

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

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)
        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a milestone {project_milestone.name} in project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )
        
        if payload.sync_linear:
            yield agg.create_message(
                "remove-milestone-message",
                data={
                    "command": "remove-project-milestone-integration",
                    "milestone_id": str(project_milestone._id),
                    "project_id": str(agg.get_aggroot().identifier),
                    "payload": {
                        "provider": "linear",
                        "external_id": str(project_milestone._id),
                        "milestone_id": str(project_milestone._id),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )


class CreateProjectCategory(Command):
    """Create Project Category - Creates a new project category"""

    class Meta:
        key = "create-project-category"
        resources = ("project",)
        tags = ["project", "category"]
        auth_required = True
        description = "Create a new project category"
        new_resource = False

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
        new_resource = False
        policy_required = False

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
        new_resource = False
        policy_required = False

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
        policy_required = True

    Data = datadef.CreateWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Create new work package"""
        result = await agg.create_work_package(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="work-package-response")


class CloneWorkPackage(Command):
    """Clone Work Package - Clones a work package"""

    class Meta:
        key = "clone-work-package"
        resources = ("work-package",)
        tags = ["work-package", "clone"]
        policy_required = True

    async def _process(self, agg, stm, payload):
        """Clone work package"""
        await agg.clone_work_package(data=payload)


class UpdateWorkPackage(Command):
    """Update Work Package - Admin can update a reusable WP"""

    class Meta:
        key = "update-work-package"
        resources = ("work-package",)
        tags = ["work-package", "update"]
        auth_required = True
        description = "Update work package"
        policy_required = True

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
        policy_required = True

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = True

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
        policy_required = True

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
        policy_required = True

    Data = datadef.UpdateProjectWorkItemPayload

    async def _process(self, agg, stm, payload):
        """Update project work item"""
        await agg.update_project_work_item(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_item = await stm.find_one(
            "project-work-item",
            where={"_id": payload.project_work_item_id}
        )

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

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

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Item Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a work item {project_work_item.name} in project {project.name}",
                    "content_type": "TEXT",
                },
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
        policy_required = True

    Data = datadef.UpdateProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Update project work package"""

        profile_id = agg.get_context().profile_id

        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        project_work_package = await stm.find_one(
            "project-work-package",
            where={"_id": payload.project_work_package_id}
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

        await agg.update_project_work_package(data=payload)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


class UpdateProjectWorkPackageWithWorkItems(Command):
    """Update Project Work Package With Work Items - Updates a project work package with work items"""

    class Meta:
        key = "update-project-work-package-with-work-items"
        resources = ("project",)
        tags = ["project", "work-package", "work-items", "update"]
        policy_required = True

    Data = datadef.UpdateProjectWorkPackageWithWorkItemsPayload

    async def _process(self, agg, stm, payload):
        """Update project work package with work items"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        project_work_package = await stm.find_one(
            "project-work-package",
            where={"_id": payload.project_work_package_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project work package {project_work_package.work_package_name} with work items",
            msglabel="update-project-work-package-with-work-items",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "work_item_ids": payload.work_item_ids,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.update_project_work_package_with_work_items(data=payload)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Updated with Work Items",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a project work package {project_work_package.work_package_name} with work items in project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


# ---------- Project Work Package Work Item (Project Context) ----------

class AddNewWorkItemToProjectWorkPackage(Command):
    """Add New Work Item to Project Work Package - Adds a new work item to a project work package"""

    class Meta:
        key = "add-new-work-item-to-project-work-package"
        resources = ("project",)
        tags = ["project", "work-package", "work-item", "add"]
        policy_required = True

    Data = datadef.AddNewWorkItemToProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Add new work item to project work package"""
        project_work_item = await agg.add_new_work_item_to_project_work_package(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_package = await stm.find_one(
            "project-work-package",
            where={"_id": payload.project_work_package_id}
        )

        work_item = await stm.find_one(
            "work-item",
            where={"_id": payload.work_item_id}
        )

        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a new work item {work_item.name} to a project work package {project_work_package.work_package_name} in project {project.name}",
            msglabel="add-new-work-item-to-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "work_item_id": work_item._id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(project_work_item), _type="project-work-item-response")

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Item Added to Project Work Package",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a new work item {work_item.name} to a project work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
            }
        )


class RemoveWorkItemFromProjectWorkPackage(Command):

    class Meta:
        key = "remove-project-work-item-from-project-work-package"
        resources = ("project",)
        tags = ["project", "work-package", "work-item", "remove"]
        policy_required = True

    Data = datadef.RemoveProjectWorkItemFromProjectWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Remove project work item from project work package"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        project_work_item = await stm.find_one(
            "project-work-item",
            where={"_id": payload.project_work_item_id,
                   "project_id": agg.get_aggroot().identifier}
        )

        project_work_package = await stm.find_one(
            "project-work-package",
            where={"_id": payload.project_work_package_id,
                   "project_id": agg.get_aggroot().identifier}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a work item {project_work_item.name} from a project work package {project_work_package.work_package_name}",
            msglabel="remove-project-work-item-from-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "project_work_item_id": project_work_item._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.remove_project_work_item_from_project_work_package(data=payload)

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Project Work Item Removed from Project Work Package",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed a work item {project_work_item.name} from a project work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
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
        policy_required = False

    Data = datadef.UpdateProjectWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Update project work item deliverable"""
        await agg.update_project_work_item_deliverable(data=payload)

        project_work_item_deliverable = await stm.find_one(
            "project-work-item-deliverable",
            where={"_id": payload.project_work_item_deliverable_id,
                   "project_id": agg.get_aggroot().identifier}
        )
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(stm, agg.get_aggroot().identifier)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Project work item deliverable updated: {project_work_item_deliverable.name}",
            msglabel="update-project-work-item-deliverable",
            msgtype=ActivityType.USER_ACTION,
            data={
                "updated_by": agg.get_context().user_id,
            }
        )

        yield agg.create_message(
            "noti-message",
            data={
                "command": "send-message",
                "payload": {
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Project Work Item Deliverable Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a project work item deliverable {project_work_item_deliverable.name} in project {project.name}",
                    "content_type": "TEXT",
                },
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
        policy_required = False

    Data = datadef.CreditUsageSummaryPayload

    async def _process(self, agg, stm, payload):
        """Get credit usage summary"""

        summary = await stm.get_credit_usage_query(
            organization_id=payload.organization_id,
        )

        yield agg.create_response({"data": [serialize_mapping(item) for item in summary]}, _type="credit-usage-summary-response")


class SyncProjectToLinear(Command):
    """Sync Project to Linear - Sync a project to Linear"""

    class Meta:
        key = "sync-project-to-linear"
        resources = ("project",)
        tags = ["project", "linear"]
        auth_required = False 
        description = "Sync a project to Linear"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Sync a project to Linear"""


        # check = await agg.check_linear_project_exists()
        # exists = check.get("exists", False)

        # if not exists:
        #     result = await agg.create_linear_project()
        # else:
        #     result = await agg.update_linear_project()

        # yield agg.create_response({"data": result}, _type="sync-project-to-linear-response")

        # project 1 -> n project_integration (provider: linear, external_id: project_id, resource: project)
        project = agg.get_rootobj()


        
        yield agg.create_message(
            "linear-message",
            data={
                "command": "sync-project-integration",
                "project": serialize_mapping(project),
                "project_id": str(agg.get_aggroot().identifier),
                "payload": {
                    "provider": "linear",
                    "external_id": str(agg.get_aggroot().identifier),
                },
                "context": {
                    "user_id": agg.get_context().user_id,
                    "profile_id": agg.get_context().profile_id,
                    "organization_id": agg.get_context().organization_id,
                    "realm": agg.get_context().realm,
                }
            }
        )

class CreateProjectIntegration(Command):
    """Create Project Integration - Create a project integration"""

    class Meta:
        key = "create-project-integration"
        resources = ("project",)
        tags = ["project", "integration"]
        auth_required = True
        description = "Create a project integration"
        policy_required = False
        internal = True

    Data = datadef.CreateProjectIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Create a project integration"""
        result = await agg.create_project_integration(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-integration-response")

class UpdateProjectIntegration(Command):
    """Update Project Integration - Update a project integration"""

    class Meta:
        key = "update-project-integration"
        resources = ("project",)
        tags = ["project", "integration"]
        auth_required = True
        description = "Update a project integration"
        policy_required = False
        internal = False

    Data = datadef.UpdateProjectIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Update a project integration"""
        await agg.update_project_integration(data=payload)


class RemoveProjectIntegration(Command):
    """Remove Project Integration - Remove a project integration"""

    class Meta:
        key = "remove-project-integration"
        resources = ("project",)
        tags = ["project", "integration"]
        auth_required = True
        description = "Remove a project integration"
        policy_required = False
        internal = False
        new_resource =True

    Data = datadef.RemoveProjectIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Remove a project integration"""
        await agg.remove_project_integration(data=payload)

class SyncProjectIntegration(Command):
    """Sync Project Integration - Sync a project integration"""

    class Meta:
        key = "sync-project-integration"
        resources = ("project",)
        tags = ["project", "integration"]
        auth_required = True
        description = "Sync a project integration"
        policy_required = False
        internal = True

    Data = datadef.SyncProjectIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Sync a project integration"""
        result = await agg.sync_project_integration(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="project-integration-response")
        
        
        

##-----------Project Milestone Integration--------------

class CreateProjectMilestoneIntegration(Command):
    """Create Project Milestone Integration - Create a project milestone integration"""
    
    class Meta:
        key = "create-project-milestone-integration"
        resources = ("project",)
        tags = ["project", "milestone", "integration"]
        auth_required = True
        description = "Create a project milestone integration"
        policy_required = False
        internal = True
        
    Data = datadef.CreateProjectMilestoneIntegrationPayload
    
    async def _process(self, agg, stm, payload):
        """Create a project milestone integration"""
        result = await agg.create_project_milestone_integration(data=payload)
        
class UpdateProjectMilestoneIntegration(Command):
    """ Update Project Milestone Integration - Update a project milestone integration"""
    
    class Meta:
        key = "update-project-milestone-integration"
        resources = ("project",)
        tags = ["project", "milestone", "integration"]
        auth_required = True
        description = "Update a project milestone integration"
        policy_required = False
        internal = True
    
    Data = datadef.UpdateProjectMilestoneIntegrationPayload
    
    async def _process(self, agg, stm, payload):
        """Update a project milestone integration"""
        await agg.update_project_milestone_integration(data=payload)
        
class RemoveProjectMilestoneIntegration(Command):
    """Remove Project Milestone Integration - Remove a project milestone integration"""
    
    class Meta:
        key = "remove-project-milestone-integration"
        resources = ("project",)
        tags = ["project", "milestone", "integration"]
        auth_required = True
        description = "Remove a project milestone integration"
        policy_required = False
        internal = True
        
    Data = datadef.RemoveProjectMilestoneIntegrationPayload
    
    async def _process(self, agg, stm, payload):
        """Remove a project milestone integration"""
        await agg.remove_project_milestone_integration(data=payload)
        
    