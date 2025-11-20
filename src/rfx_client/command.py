from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXClientDomain
from . import datadef, config
from .helper import get_project_member_user_ids, _handle_mentions


from rfx_integration.pm_service import PMService
from rfx_integration.pm_service.base import (
    CreateTicketPayload,
    UpdateTicketPayload as PMUpdatePayload,
    CreateProjectPayload as PMProjectPayload,
    CreateCommentPayload as PMCreateCommentPayload,
    UpdateCommentPayload as PMUpdateCommentPayload,
    UpdateProjectPayload as PMUpdateProjectPayload,
    CreateProjectMilestonePayload as PMCreateMilestonePayload,
    UpdateProjectMilestonePayload as PMUpdateMilestonePayload,
)


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
            },
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
        yield agg.create_response(
            serialize_mapping(new_project), _type="project-response"
        )

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
            },
        )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                async with PMService.init_client(
                    provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                ) as pm_service:
                    pm_payload = PMProjectPayload(
                        name=new_project.name,
                        description=getattr(new_project, "description", None),
                        lead_id=str(profile_id) if profile_id else None,
                        state=getattr(new_project, "status", "PLANNED"),
                        start_date=getattr(new_project, "start_date", None).isoformat(),
                        target_date=getattr(
                            new_project, "target_date", None
                        ).isoformat(),
                        project_id=str(new_project._id),
                    )
                    pm_response = await pm_service.create_project(pm_payload)
                    await agg.create_project_integration(
                        data=datadef.CreateProjectIntegrationPayload(
                            provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                            external_id=pm_response.external_id,
                            external_url=pm_response.url,
                        )
                    )
            except Exception as e:
                logger.error(f"✗ Failed to sync project: {str(e)}")


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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project {project.name}",
            msglabel="update-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": project.name,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        message_subject = "Project Updated"
        if project.status == "DRAFT":
            message_subject = "Estimator Updated"

        message_content = f"{profile.name__given} {profile.name__family} updated a project {project.name}"
        if project.status == "DRAFT":
            message_content = f"{profile.name__given} {profile.name__family} updated an estimator {project.name}"

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": message_subject,
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": message_content,
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
            )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                integration = await stm.find_one(
                    "project_integration",
                    where=dict(
                        project_id=agg.get_aggroot().identifier,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMUpdateProjectPayload(
                            external_id=integration.external_id,
                            name=payload.name if payload.name else None,
                            description=payload.description,
                            state=getattr(payload, "status", None),
                            lead_id=str(getattr(payload, "lead_id", None)),
                            target_date=getattr(
                                payload, "target_date", None
                            ).isoformat(),
                        )
                        pm_response = await pm_service.update_project(pm_payload)
                        await agg.update_project_integration(
                            data=datadef.UpdateProjectIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id,
                                external_url=pm_response.external_url,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to sync update to PM service: {str(e)}")


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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a project {project.name}",
            msglabel="delete-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_name": project.name,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Project Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
            )
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                integration = await stm.find_one(
                    "project_integration",
                    where=dict(
                        project_id=agg.get_aggroot().identifier,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        await pm_service.delete_project(
                            project_id=integration.external_id,
                            permanently=True,
                        )
                        await agg.remove_project_integration(
                            data=datadef.RemoveProjectIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to remove from PM service: {str(e)}")
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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} applied a promotion code {payload.promotion_code} to estimator {project.name}",
            msglabel="apply-promotion",
            msgtype=ActivityType.USER_ACTION,
            data={
                "promotion_code": payload.promotion_code,
                "applied_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Promotion Applied",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} applied a promotion code {payload.promotion_code}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

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
            },
        )
        yield agg.create_response(
            serialize_mapping(result), _type="project-bdm-contact-response"
        )
        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Created",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} created a BDM contact for project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a BDM contact",
            msglabel="update-project-bdm-contact",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_bdm_contact_id": payload.bdm_contact_id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a BDM contact of project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a BDM contact of project {project.name}",
            msglabel="delete-project-bdm-contact",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_bdm_contact_id": payload.bdm_contact_id,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        await agg.delete_project_bdm_contact(data=payload)
        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "BDM Contact Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a BDM contact of project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
            },
        )

        yield agg.create_response(
            serialize_mapping(result), _type="project-work-package-response"
        )

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )
        if project.status == "DRAFT":
            project_name = f"estimator {project.name}"
        else:
            project_name = f"project {project.name}"

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a work package to {project_name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
            },
        )

        await agg.remove_work_package_from_estimator(data=payload)

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        if project.status == "DRAFT":
            project_name = f"estimator {project.name}"
        else:
            project_name = f"project {project.name}"

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Removed",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed a work package from {project_name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
            },
        )

        yield agg.create_response(serialize_mapping(result), _type="project-response")


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
            member_id=payload.member_id, role=payload.role
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
            },
        )

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )
        member = await stm.get_profile(payload.member_id)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Added",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added {member.name__given} {member.name__family} to project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )
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
            },
        )

        await agg.update_project_member(member_id=payload.member_id, role=payload.role)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Role Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated {member.name__given} {member.name__family}'s role in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )
        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a member",
            msglabel="remove-member-from-project",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": payload.member_id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.remove_project_member(member_id=payload.member_id)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Member Removed",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed {member.name__given} {member.name__family} from project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a milestone '{result.name}'",
            msglabel="create-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": result._id,
                "milestone_name": result.name,
                "created_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        yield agg.create_response(
            serialize_mapping(result), _type="project-milestone-response"
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Created",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} created a milestone '{result.name}' for project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
            )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                project_integration = await stm.find_one(
                    "project_integration",
                    where=dict(
                        project_id=agg.get_aggroot().identifier,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if project_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMCreateMilestonePayload(
                            name=result.name,
                            project_id=project_integration.external_id,
                            description=getattr(result, "description", None),
                            target_date=getattr(result, "target_date", None),
                            sort_order=getattr(result, "sort_order", None),
                        )
                        pm_response = await pm_service.create_project_milestone(
                            pm_payload
                        )
                        await agg.create_project_milestone_integration(
                            data=datadef.CreateProjectMilestoneIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=pm_response.external_id,
                                milestone_id=str(result._id),
                                project_id=str(agg.get_aggroot().identifier),
                                external_url=pm_response.external_url,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to sync milestone: {str(e)}")


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
            "project_milestone", where={"_id": payload.milestone_id}
        )
        if not project_milestone:
            raise ValueError(
                f"Project milestone with ID {payload.milestone_id} not found."
            )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a milestone {project_milestone.name}",
            msglabel="update-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": payload.milestone_id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.update_project_milestone(data=payload)

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a milestone {project_milestone.name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
            )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                milestone_integration = await stm.find_one(
                    "project_milestone_integration",
                    where=dict(
                        milestone_id=payload.milestone_id,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if milestone_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMUpdateMilestonePayload(
                            external_id=milestone_integration.external_id,
                            name=getattr(payload, "name", None),
                            description=getattr(payload, "description", None),
                            target_date=getattr(payload, "target_date", None),
                            sort_order=getattr(payload, "sort_order", None),
                        )
                        pm_response = await pm_service.update_project_milestone(
                            pm_payload
                        )
                        await agg.update_project_milestone_integration(
                            data=datadef.UpdateProjectMilestoneIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=milestone_integration.external_id,
                                milestone_id=str(payload.milestone_id),
                                project_id=str(agg.get_aggroot().identifier),
                                external_url=pm_response.external_url,
                            )
                        )

            except Exception as e:
                logger.error(f"✗ Failed to sync milestone update: {str(e)}")


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
            "project_milestone", where={"_id": payload.milestone_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} deleted a milestone",
            msglabel="delete-project-milestone",
            msgtype=ActivityType.USER_ACTION,
            data={
                "milestone_id": payload.milestone_id,
                "deleted_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.delete_project_milestone(data=payload)

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Milestone Deleted",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} deleted a milestone {project_milestone.name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
            )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                milestone_integration = await stm.find_one(
                    "project_milestone_integration",
                    where=dict(
                        milestone_id=payload.milestone_id,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )

                if milestone_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        await pm_service.delete_project_milestone(
                            external_id=milestone_integration.external_id
                        )
                        await agg.remove_project_milestone_integration(
                            data=datadef.RemoveProjectMilestoneIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=milestone_integration.external_id,
                                milestone_id=str(payload.milestone_id),
                                project_id=str(agg.get_aggroot().identifier),
                            )
                        )

            except Exception as e:
                logger.error(f"✗ Failed to delete milestone from PM service: {str(e)}")


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
        yield agg.create_response(
            serialize_mapping(result), _type="project-category-response"
        )


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
        resources = ("work_package",)
        tags = ["work-package", "create"]
        new_resource = True
        auth_required = True
        description = "Create new work package"
        policy_required = True

    Data = datadef.CreateWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Create new work package"""
        result = await agg.create_work_package(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="work-package-response"
        )


class CloneWorkPackage(Command):
    """Clone Work Package - Clones a work package"""

    class Meta:
        key = "clone-work-package"
        resources = ("work_package",)
        tags = ["work-package", "clone"]
        policy_required = True

    async def _process(self, agg, stm, payload):
        """Clone work package"""
        await agg.clone_work_package(data=payload)


class UpdateWorkPackage(Command):
    """Update Work Package - Admin can update a reusable WP"""

    class Meta:
        key = "update-work-package"
        resources = ("work_package",)
        tags = ["work-package", "update"]
        auth_required = True
        description = "Update work package"
        policy_required = True

    Data = datadef.UpdateWorkPackagePayload

    async def _process(self, agg, stm, payload):
        """Update work package"""
        update_data = payload.dict(exclude_none=True)
        result = await agg.update_work_package(update_data)
        yield agg.create_response(
            serialize_mapping(result), _type="work-package-response"
        )


class DeleteWorkPackage(Command):
    """Invalidate Work Package - Invalidate a work package"""

    class Meta:
        key = "delete-work-package"
        resources = ("work_package",)
        tags = ["work-package", "delete"]
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
        resources = ("work_item",)
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
        resources = ("work_item",)
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
        resources = ("work_item",)
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
        resources = ("work_item",)
        tags = ["work-item", "type", "reference"]
        new_resource = True
        policy_required = False

    Data = datadef.CreateWorkItemTypePayload

    async def _process(self, agg, stm, payload):
        """Create new work item type"""
        result = await agg.create_work_item_type(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="work-item-type-response"
        )


class UpdateWorkItemType(Command):
    """Update Work Item Type - Updates a work item type"""

    class Meta:
        key = "update-work-item-type"
        resources = ("work_item",)
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
        resources = ("work_item",)
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
        resources = ("work_item",)
        tags = ["work-item", "deliverable", "create"]
        new_resource = True
        auth_required = True
        description = "Create new work package deliverable"
        policy_required = False

    Data = datadef.CreateWorkItemDeliverablePayload

    async def _process(self, agg, stm, payload):
        """Create new work item deliverable"""
        result = await agg.create_work_item_deliverable(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="work-item-deliverable-response"
        )


class UpdateWorkItemDeliverable(Command):
    class Meta:
        key = "update-work-item-deliverable"
        resources = ("work_item",)
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
        resources = ("work_item",)
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
        resources = ("work_package",)
        tags = ["work-package", "work-item", "add"]
        policy_required = True

    Data = datadef.AddWorkItemToWorkPackagePayload

    async def _process(self, agg, stm, payload):
        await agg.add_work_item_to_work_package(payload.work_item_id)


class RemoveWorkItemFromWorkPackage(Command):
    """Remove Work Item from Work Package - Removes a work item from a work package"""

    class Meta:
        key = "remove-work-item-from-work-package"
        resources = ("work_package",)
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
            "project-work-item", where={"_id": payload.project_work_item_id}
        )

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project work item {project_work_item.name}",
            msglabel="update-project-work-item",
            msgtype=ActivityType.USER_ACTION,
            data={
                "work_item_id": project_work_item._id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Item Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a work item {project_work_item.name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        project_work_package = await stm.find_one(
            "project-work-package", where={"_id": payload.project_work_package_id}
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a project work package {project_work_package.work_package_name}",
            msglabel="update-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.update_project_work_package(data=payload)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        project_work_package = await stm.find_one(
            "project-work-package", where={"_id": payload.project_work_package_id}
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
            },
        )

        await agg.update_project_work_package_with_work_items(data=payload)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Package Updated with Work Items",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a project work package {project_work_package.work_package_name} with work items in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        project_work_item = await agg.add_new_work_item_to_project_work_package(
            data=payload
        )

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        project_work_package = await stm.find_one(
            "project-work-package", where={"_id": payload.project_work_package_id}
        )

        work_item = await stm.find_one("work-item", where={"_id": payload.work_item_id})

        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a new work item {work_item.name} to a project work package {project_work_package.work_package_name} in project {project.name}",
            msglabel="add-new-work-item-to-project-work-package",
            msgtype=ActivityType.USER_ACTION,
            data={
                "project_work_package_id": project_work_package._id,
                "work_item_id": work_item._id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        yield agg.create_response(
            serialize_mapping(project_work_item), _type="project-work-item-response"
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Item Added to Project Work Package",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} added a new work item {work_item.name} to a project work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        project_work_item = await stm.find_one(
            "project-work-item",
            where={
                "_id": payload.project_work_item_id,
                "project_id": agg.get_aggroot().identifier,
            },
        )

        project_work_package = await stm.find_one(
            "project-work-package",
            where={
                "_id": payload.project_work_package_id,
                "project_id": agg.get_aggroot().identifier,
            },
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
            },
        )

        await agg.remove_project_work_item_from_project_work_package(data=payload)

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Work Item Removed from Project Work Package",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} removed a work item {project_work_item.name} from a project work package {project_work_package.work_package_name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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
            where={
                "_id": payload.project_work_item_deliverable_id,
                "project_id": agg.get_aggroot().identifier,
            },
        )
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)
        user_ids, project = await get_project_member_user_ids(
            stm, agg.get_aggroot().identifier
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Project work item deliverable updated: {project_work_item_deliverable.name}",
            msglabel="update-project-work-item-deliverable",
            msgtype=ActivityType.USER_ACTION,
            data={
                "updated_by": agg.get_context().user_id,
            },
        )

        if config.MESSAGE_ENABLED:
            context = agg.get_context()
            service_proxy = context.service_proxy
            logger.info(f"service proxy: {service_proxy}")
            await service_proxy.msg_client.send(
                f"{config.MESSAGE_NAMESPACE}:send-message",
                command="send-message",
                resource="message",
                payload={
                    "recipients": [str(user_id) for user_id in user_ids],
                    "subject": "Project Work Item Deliverable Updated",
                    "message_type": "NOTIFICATION",
                    "priority": "MEDIUM",
                    "content": f"{profile.name__given} {profile.name__family} updated a project work item deliverable {project_work_item_deliverable.name} in project {project.name}",
                    "content_type": "TEXT",
                },
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id),
                        "profile_id": str(context.profile_id),
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    }
                },
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

        yield agg.create_response(
            {"data": [serialize_mapping(item) for item in summary]},
            _type="credit-usage-summary-response",
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
        yield agg.create_response(
            serialize_mapping(result), _type="project-integration-response"
        )


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
        new_resource = True

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
        yield agg.create_response(
            serialize_mapping(result), _type="project-integration-response"
        )


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
        await agg.create_project_milestone_integration(data=payload)


class UpdateProjectMilestoneIntegration(Command):
    """Update Project Milestone Integration - Update a project milestone integration"""

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


### Ticket Command


# ---------- Inquiry (Ticket Context) ----------
class CreateInquiry(Command):
    """Create Inquiry - Creates a new inquiry (ticket not tied to project)"""

    class Meta:
        key = "create-inquiry"
        resources = ("ticket",)
        tags = ["ticket", "inquiry"]
        auth_required = True
        description = "Create a new inquiry"
        new_resource = True
        policy_required = True

    Data = datadef.CreateInquiryPayload

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.create_inquiry(data=payload)

        yield agg.create_activity(
            logroot=AggregateRoot(
                resource="ticket",
                identifier=result._id,
                domain_sid=agg.get_aggroot().domain_sid,
                domain_iid=agg.get_aggroot().domain_iid,
            ),
            message=f"{profile.name__given} {profile.name__family} created a inquiry {result.title}",
            msglabel="create inquiry",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": result._id,
                "ticket_title": result.title,
                "created_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class CreateInquiryDraft(Command):
    """save inquiry as draft (status = draft)"""

    class Meta:
        key = "create-inquiry-draft"
        resources = ("ticket",)
        tags = ["ticket", "inquiry", "draft"]
        auth_required = True
        description = "Create a new inquiry draft"
        new_resource = True
        policy_required = False

    Data = datadef.CreateInquiryPayload

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.create_inquiry_draft(data=payload)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a ticket {result.title}",
            msglabel="create ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "created_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class CloseInquiry(Command):
    """Close Inquiry - BDM closes inquiry(OPEN/DISCUSSSION -> CLOSED)"""

    class Meta:
        key = "close-inquiry"
        resources = ("ticket",)
        tags = ["ticket", "inquiry", "close"]
        auth_required = True
        description = "Close an inquiry"
        policy_required = False

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.close_inquiry()

        yield agg.create_activity(
            logroot=AggregateRoot(
                resource="ticket",
                identifier=result._id,
                domain_sid=agg.get_aggroot().domain_sid,
                domain_iid=agg.get_aggroot().domain_iid,
            ),
            message=f"{profile.name__given} {profile.name__family} closed inquiry {result.title}",
            msglabel="close inquiry",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": result._id,
                "ticket_title": result.title,
                "closed_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class SubmitInquiryDraft(Command):
    """submit inquiry draft - change status from DRAFT to OPEN"""

    class Meta:
        key = "submit-inquiry-draft"
        resources = ("ticket",)
        tags = ["ticket", "inquiry", "submit", "draft"]
        auth_required = True
        description = "Submit an inquiry draft"
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.submit_inquiry_draft()

        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


# ---------- Ticket (Ticket Context) ----------
class CreateTicket(Command):
    """Create Ticket - Creates a new ticket tied to a project"""

    class Meta:
        key = "create-ticket"
        resources = ("ticket",)
        tags = ["ticket"]
        auth_required = True
        description = "Create a new ticket in project"
        new_resource = True
        internal = False
        policy_required = False

    Data = datadef.CreateTicketPayload

    async def _process(self, agg, stm, payload):
        """Create a new ticket in project"""
        result = await agg.create_ticket(data=payload)
        await agg.add_ticket_to_project(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a ticket {result.title}",
            msglabel="create ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "created_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                async with PMService.init_client(
                    provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                ) as pm_service:
                    pm_payload = CreateTicketPayload(
                        ticket_id=str(result._id),
                        title=payload.title,
                        description=payload.description,
                        assignee_id=str(payload.assignee),
                        priority=payload.priority,
                        project_id=str(payload.project_id),
                    )
                    pm_response = await pm_service.create_ticket(pm_payload)
                    await agg.create_ticket_integration(
                        data=datadef.CreateTicketIntegrationPayload(
                            provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                            external_id=pm_response.external_id,
                            external_url=pm_response.url,
                        )
                    )

            except Exception as e:
                logger.error(f"Failed to sync ticket to Linear: {str(e)}")

        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class UpdateTicketInfo(Command):
    """Update Ticket Info - Updates ticket information"""

    class Meta:
        key = "update-ticket"
        resources = ("ticket",)
        tags = ["ticket", "update"]
        auth_required = True
        description = "Update ticket information"
        policy_required = False

    Data = datadef.UpdateTicketPayload

    async def _process(self, agg, stm, payload):
        await agg.update_ticket_info(payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        ticket = await stm.find_one(
            "ticket", where=dict(_id=agg.get_aggroot().identifier)
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a ticket {ticket.title}",
            msglabel="update ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                integration = await stm.find_one(
                    "ticket_integration",
                    where=dict(
                        ticket_id=agg.get_aggroot().identifier,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )

                if integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMUpdatePayload(
                            external_id=integration.external_id,
                            title=getattr(payload, "title", None),
                            description=getattr(payload, "description", None),
                            status_id=str(getattr(payload, "status", None)),
                            assignee_id=str(getattr(payload, "assignee", None)),
                            priority=getattr(payload, "priority", None),
                        )
                        pm_response = await pm_service.update_ticket(pm_payload)
                        await agg.update_ticket_integration(
                            data=datadef.UpdateTicketIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id,
                                external_url=pm_response.external_url,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to sync update to PM service: {str(e)}")

        ticket_update = await stm.find_one(
            "ticket", where=dict(_id=agg.get_aggroot().identifier)
        )

        yield agg.create_response(
            serialize_mapping(ticket_update), _type="ticket-response"
        )


class RemoveTicket(Command):
    """Remove Ticket - Removes a ticket"""

    class Meta:
        key = "remove-ticket"
        resources = ("ticket",)
        tags = ["ticket", "remove"]
        auth_required = True
        description = "Remove ticket"
        policy_required = False

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        ticket = await stm.find_one(
            "ticket", where=dict(_id=agg.get_aggroot().identifier)
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a ticket {ticket.title}",
            msglabel="remove ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "removed_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                integration = await stm.find_one(
                    "ticket_integration",
                    where=dict(
                        ticket_id=agg.get_aggroot().identifier,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )

                if integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        await pm_service.delete_ticket(
                            external_id=integration.external_id,
                            permanently=True,
                        )

                        await agg.remove_ticket_integration(
                            data=datadef.RemoveTicketIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id,
                            )
                        )

            except Exception as e:
                logger.error(f"✗ Failed to remove from PM service: {str(e)}")

        await agg.remove_ticket()


# ---------- Ticket Assignee (Ticket Context) ----------
class AssignMemberToTicket(Command):
    """Assign Member to Ticket - Assigns a member to ticket"""

    class Meta:
        key = "assign-member"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Assign member to ticket"
        policy_required = True

    Data = datadef.AssignTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Assign member to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} assigned {member.name__given} {member.name__family}",
            msglabel="assign member",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": member._id,
                "assigned_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.assign_member_to_ticket(data=payload)


class RemoveMemberFromTicket(Command):
    """Remove Member from Ticket - Removes a member from ticket"""

    class Meta:
        key = "remove-member-ticket"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Remove member from ticket"
        policy_required = True

    Data = datadef.RemoveTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed {member.name__given} {member.name__family}",
            msglabel="remove member",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": member._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.remove_member_from_ticket(payload.member_id)


# ---------- Ticket Participant (Ticket Context) ----------
class AddParticipantToTicket(Command):
    """Add Participant to Ticket - Adds a participant to ticket"""

    class Meta:
        key = "add-participant"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Add participant to ticket"
        policy_required = True

    Data = datadef.AddTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Add participant to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        participant = await stm.get_profile(payload.participant_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added {participant.name__given} {participant.name__family} as a participant",
            msglabel="add participant",
            msgtype=ActivityType.USER_ACTION,
            data={
                "participant_id": participant._id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.add_ticket_participant(payload.participant_id)


class RemoveParticipantFromTicket(Command):
    """Remove Participant from Ticket - Removes a participant from ticket"""

    class Meta:
        key = "remove-participant"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Remove participant from ticket"
        policy_required = True

    Data = datadef.RemoveTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Remove participant from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        participant = await stm.get_profile(payload.participant_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a participant {participant.name__given} {participant.name__family}",
            msglabel="remove participant",
            msgtype=ActivityType.USER_ACTION,
            data={
                "participant_id": participant._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.remove_ticket_participant(payload.participant_id)


# ---------- Tag Context ----------
class CreateTag(Command):
    """Create Tag - Creagtes a new tag"""

    class Meta:
        key = "create-tag"
        resources = ("tag",)
        tags = ["tag"]
        auth_required = True
        description = "Create a new tag in project"
        new_resource = True
        policy_required = False

    Data = datadef.CreateTagPayload

    async def _process(self, agg, stm, payload):
        """Create tag"""
        result = await agg.create_tag(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="tag-response")


class UpdateTag(Command):
    """Update Tag - Updates a tag"""

    class Meta:
        key = "update-tag"
        resources = ("tag",)
        tags = ["tag", "update"]
        auth_required = True
        description = "Update tag"
        policy_required = False

    Data = datadef.UpdateTagPayload

    async def _process(self, agg, stm, payload):
        """Update tag"""
        await agg.update_tag(data=payload)


class DeleteTag(Command):
    """Delete Tag - Deletes a tag"""

    class Meta:
        key = "delete-tag"
        resources = ("tag",)
        tags = ["tag", "delete"]
        auth_required = True
        description = "Delete tag"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Delete tag"""
        await agg.delete_tag()


# ---------- Ticket Type (Ticket Context) ----------
class CreateTicketType(Command):
    """Create Ticket Type - Creates a new ticket type"""

    class Meta:
        key = "create-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "reference"]
        auth_required = True
        description = "Create a new ticket type"
        new_resource = True
        policy_required = False

    Data = datadef.CreateTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Create ticket type"""
        result = await agg.create_ticket_type(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="ticket-type-response"
        )


class UpdateTicketType(Command):
    """Update Ticket Type - Updates a ticket type"""

    class Meta:
        key = "update-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "update"]
        auth_required = True
        description = "Update a ticket type"
        new_resource = True
        policy_required = False

    Data = datadef.UpdateTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Update ticket type"""
        await agg.update_ticket_type(data=payload)


class DeleteTicketType(Command):
    """Delete Ticket Type - Deletes a ticket type"""

    class Meta:
        key = "delete-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "delete"]
        auth_required = True
        description = "Delete a ticket type"
        new_resource = True
        policy_required = False

    Data = datadef.DeleteTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Delete ticket type"""
        await agg.delete_ticket_type(data=payload)


# ---------- Ticket Tag (Ticket Context) ----------
class AddTicketTag(Command):
    """Add Tag to Ticket - Adds a tag to ticket"""

    class Meta:
        key = "add-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Add tag to ticket"
        policy_required = True

    Data = datadef.AddTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Add tag to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a tag",
            msglabel="add tag",
            msgtype=ActivityType.USER_ACTION,
            data={
                "tag_id": payload.tag_id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            },
        )
        await agg.add_ticket_tag(payload.tag_id)


class RemoveTicketTag(Command):
    """Remove Tag from Ticket - Removes a tag from ticket"""

    class Meta:
        key = "remove-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Remove tag from ticket"
        policy_required = True

    Data = datadef.RemoveTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Remove tag from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a tag",
            msglabel="remove tag",
            msgtype=ActivityType.USER_ACTION,
            data={
                "tag_id": payload.tag_id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            },
        )

        await agg.remove_ticket_tag(payload.tag_id)


# ------------ Status Context ----------
class CreateStatus(Command):
    """Create Status - Creates a new status"""

    class Meta:
        key = "create-status"
        resources = ("status",)
        tags = ["status"]
        auth_required = True
        description = "Create a new status"
        new_resource = True
        policy_required = False

    Data = datadef.CreateStatusPayload

    async def _process(self, agg, stm, payload):
        """Create status"""
        status = await agg.create_status(data=payload)
        yield agg.create_response(serialize_mapping(status), _type="status-response")


class CreateStatusKey(Command):
    """Create Status Key - Creates a new status key"""

    class Meta:
        key = "create-status-key"
        resources = ("status",)
        tags = ["status", "status-key"]
        auth_required = True
        description = "Create a new status key"
        policy_required = False

    Data = datadef.CreateStatusKeyPayload

    async def _process(self, agg, stm, payload):
        """Create status key"""
        status_key = await agg.create_status_key(data=payload)
        yield agg.create_response(
            serialize_mapping(status_key), _type="status-key-response"
        )


class CreateStatusTransition(Command):
    """Create Status Transition - Creates a new status transition"""

    class Meta:
        key = "create-status-transition"
        resources = ("status",)
        tags = ["status", "status-transition"]
        auth_required = True
        description = "Create a new status transition"
        policy_required = False

    Data = datadef.CreateStatusTransitionPayload

    async def _process(self, agg, stm, payload):
        """Create status transition"""
        status_transition = await agg.create_status_transition(data=payload)
        yield agg.create_response(
            serialize_mapping(status_transition), _type="status-transition-response"
        )


# --------------- Ticket Integration------------


class CreateTicketIntegration(Command):
    """Create Ticket Integration"""

    class Meta:
        key = "create-ticket-integration"
        resources = ("ticket",)
        tags = ["ticket", "integration"]
        auth_required = True
        description = "Create a ticket integration"
        policy_required = False
        internal = True

    Data = datadef.CreateTicketIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Create a ticket integration"""
        await agg.create_ticket_integration(data=payload)


class UpdateTicketIntegration(Command):
    """Update Ticket Integration - Update a ticket integration"""

    class Meta:
        key = "update-ticket-integration"
        resources = ("ticket",)
        tags = ["ticket", "integration"]
        auth_required = True
        description = "Update a ticket integration"
        policy_required = False
        internal = True

    Data = datadef.UpdateTicketIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Update a ticket integration"""
        await agg.update_ticket_integration(data=payload)


class RemoveTicketIntegration(Command):
    """Remove Ticket Integration - Remove a ticket integration"""

    class Meta:
        key = "remove-ticket-integration"
        resources = ("ticket",)
        tags = ["ticket", "integration"]
        auth_required = True
        description = "Remove a ticket integration"
        policy_required = False
        internal = True

    Data = datadef.RemoveTicketIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Remove a ticket integration"""
        await agg.remove_ticket_integration(data=payload)


# ---------- Comment Context ----------


class CreateComment(Command):
    """
    Create Comment - Creates a new comment
    API Endpoint Example:
        - Endpoint: POST /api/v1/namespace:create-comment/<aggroot>/<aggroot_id>
        - Sample:
            + aggroot = project, aggroot_id = <project_id>
            + aggroot = ticket, aggroot_id = <ticket_id>
        - Data: resource = project/ticket, resource_id = <project_id>/<ticket_id>, content = "This is a comment", sync_linear = True/False

    """

    class Meta:
        key = "create-comment"
        resources: tuple(config.COMMENT_AGGROOTS.split(","))
        tags = ["comment"]
        auth_required = True
        description = "Create a new comment"
        policy_required = True

    Data = datadef.CreateCommentPayload

    async def _process(self, agg, stm, payload):
        """Create comment"""

        aggroot = agg.get_aggroot()
        resource_type = aggroot.resource
        resource_id = aggroot.identifier

        payload_dict = serialize_mapping(payload)
        payload_dict["resource"] = resource_type
        payload_dict["resource_id"] = str(resource_id)
        payload_dict["source"] = "user"

        result = await agg.create_comment(data=payload_dict)
        await _handle_mentions(agg, stm, payload.content)

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and resource_type != "project":
            try:
                if not config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER:
                    raise ValueError(
                        "PROJECT_MANAGEMENT_INTEGRATION_PROVIDER is not set"
                    )
                integration_table = f"{resource_type}_integration"
                resource_integration = await stm.find_one(
                    integration_table,
                    where=dict(
                        **{f"{resource_type}_id": resource_id},
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if resource_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMCreateCommentPayload(
                            body=result.content,
                            target_id=resource_integration.external_id,
                            comment_id=str(result._id),
                            parent_id=None,
                            resource_type=resource_type,
                        )
                        pm_response = await pm_service.create_comment(pm_payload)
                        await agg.create_comment_integration(
                            data=datadef.CreateCommentIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=pm_response.external_id,
                                external_url=pm_response.url,
                                comment_id=result._id,
                                source="user",
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to sync comment: {str(e)}")
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


class UpdateComment(Command):
    """Update Comment - Updates a comment"""

    class Meta:
        key = "update-comment"
        resources = ("comment",)
        tags = ["comment", "update"]
        auth_required = True
        description = "Update a comment"
        policy_required = True

    Data = datadef.UpdateCommentPayload

    async def _process(self, agg, stm, payload):
        """Update comment"""
        await agg.update_comment(data=payload)
        await _handle_mentions(agg, stm, payload.content)

        updated_comment = await stm.find_one(
            "comment", where=dict(_id=agg.get_aggroot().identifier)
        )
        aggroot = agg.get_aggroot()
        resource_type = aggroot.resource
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and resource_type != "project":
            try:
                if not config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER:
                    raise ValueError(
                        "PROJECT_MANAGEMENT_INTEGRATION_PROVIDER is not set"
                    )

                comment_integration = await stm.find_one(
                    "comment_integration",
                    where=dict(
                        comment_id=updated_comment._id,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if comment_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMUpdateCommentPayload(
                            external_id=comment_integration.external_id,
                            body=updated_comment.content,
                        )
                        pm_response = await pm_service.update_comment(pm_payload)
                        await agg.update_comment_integration(
                            data=datadef.UpdateCommentIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=comment_integration.external_id,
                                external_url=pm_response.external_url
                                if hasattr(pm_response, "external_url")
                                else comment_integration.external_url,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to sync comment update: {str(e)}")
        yield agg.create_response(
            serialize_mapping(updated_comment), _type="comment-response"
        )


class DeleteComment(Command):
    """Delete Comment - Deletes a comment"""

    class Meta:
        key = "delete-comment"
        resources = ("comment",)
        tags = ["comment", "delete"]
        auth_required = True
        description = "Delete a comment"
        policy_required = True

    async def _process(self, agg, stm, payload):
        """Delete comment"""
        comment_id = agg.get_aggroot().identifier
        await stm.find_one("comment", where=dict(_id=comment_id))
        resource_type = agg.get_aggroot().resource

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and resource_type != "project":
            try:
                if not config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER:
                    raise ValueError(
                        "PROJECT_MANAGEMENT_INTEGRATION_PROVIDER is not set"
                    )
                comment_integration = await stm.find_one(
                    "comment_integration",
                    where=dict(
                        comment_id=comment_id,
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if comment_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        await pm_service.delete_comment(
                            external_id=comment_integration.external_id
                        )
                        await agg.remove_comment_integration(
                            data=datadef.RemoveCommentIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=comment_integration.external_id,
                                comment_id=comment_id,
                            )
                        )
            except Exception as e:
                logger.error(f"✗ Failed to delete from PM service: {str(e)}")
        await agg.delete_comment()


class ReplyComment(Command):
    """Reply to Comment - Replies to a comment"""

    class Meta:
        key = "reply-comment"
        resources = ("comment",)
        tags = ["comment", "reply"]
        auth_required = True
        description = "Reply to a comment"
        policy_required = True

    Data = datadef.ReplyToCommentPayload

    async def _process(self, agg, stm, payload):
        """Reply to comment"""
        comment_parent_id = agg.get_aggroot().identifier
        comment_parent = await stm.find_one(
            "comment", where=dict(_id=comment_parent_id)
        )
        resource_type = comment_parent.resource
        resource_id = comment_parent.resource_id

        payload_dict = serialize_mapping(payload)
        payload_dict["resource"] = resource_type
        payload_dict["resource_id"] = str(resource_id)
        payload_dict["source"] = "user"

        result = await agg.reply_to_comment(data=payload_dict)

        await _handle_mentions(agg, stm, payload.content)

        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and resource_type != "project":
            try:
                if not config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER:
                    raise ValueError(
                        "PROJECT_MANAGEMENT_INTEGRATION_PROVIDER is not set"
                    )
                integration_table = f"{resource_type}_integration"
                resource_integration = await stm.find_one(
                    integration_table,
                    where=dict(
                        **{f"{resource_type}_id": resource_id},
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                    ),
                )
                if resource_integration:
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        pm_payload = PMCreateCommentPayload(
                            body=result.content,
                            target_id=resource_integration.external_id,
                            comment_id=str(result._id),
                            parent_id=str(comment_parent._id),
                            resource_type=resource_type,
                        )
                        pm_response = await pm_service.create_comment(pm_payload)
                        await agg.create_comment_integration(
                            data=datadef.CreateCommentIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=pm_response.external_id,
                                external_url=pm_response.url,
                                comment_id=result._id,
                                source="user",
                            )
                        )

            except Exception as e:
                logger.error(f"✗ Failed to sync comment reply: {str(e)}")
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


class AttachFileToComment(Command):
    """Attach File to Comment - Attaches a file to a comment after upload"""

    class Meta:
        key = "attach-file"
        resources = ("comment",)
        tags = ["comment", "attachment"]
        auth_required = True
        description = "Attach file to comment after upload"
        policy_required = False

    Data = datadef.AttachFileToCommentPayload

    async def _process(self, agg, stm, payload):
        """Attach file to comment"""
        result = await agg.attach_file_to_comment(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="comment-attach-response"
        )


class UpdateAttachment(Command):
    """Update Attachment - Updates attachment metadata"""

    class Meta:
        key = "update-attachment"
        resources = ("comment",)
        tags = ["comment", "attachment", "update"]
        auth_required = True
        description = "Update attachment metadata"
        policy_required = False

    Data = datadef.UpdateAttachmentPayload

    async def _process(self, agg, stm, payload):
        """Update attachment"""
        comment = agg.get_aggroot()
        if not comment:
            raise ValueError(f"Comment not found: {agg.get_aggroot().identifier}")
        await agg.update_attachment(data=payload)
        yield agg.create_response(
            {"status": "success"}, _type="comment-attach-response"
        )


class DeleteAttachment(Command):
    """Delete Attachment - Deletes an attachment from a comment"""

    class Meta:
        key = "delete-attachment"
        resources = ("comment",)
        tags = ["comment", "attachment", "delete"]
        auth_required = True
        description = "Delete attachment from comment"
        policy_required = False

    Data = datadef.DeleteAttachmentPayload

    async def _process(self, agg, stm, payload):
        """Delete attachment"""

        comment = agg.get_aggroot()
        if not comment:
            raise ValueError(f"Comment not found: {agg.get_aggroot().identifier}")

        await agg.delete_attachment(data=payload)
        yield agg.create_response(
            {"status": "success"}, _type="comment-attach-response"
        )


class CreateReactionComment(Command):
    """Add Reaction for comment"""

    class Meta:
        key = "create-reaction-comment"
        resource = ("comment",)
        tags = ["comment", "reaction"]
        auth_required = True
        description = "Add reaction for comment"
        policy_required = False

    Data = datadef.CreateReactionCommentPayload

    async def _process(self, agg, stm, payload):
        """Add reaction for comment"""

        result = await agg.create_reaction_comment(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="comment-reaction-response"
        )


class RemoveReactionComment(Command):
    """Remove Reaction for comment"""

    class Meta:
        key = "remove-reaction-comment"
        resource = ("comment",)
        tags = ["comment", "reaction"]
        auth_required = True
        description = "Remove reaction for comment"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Remove reaction for comment"""
        await agg.remove_reaction()
        yield agg.create_response(
            {"status": "success"}, _type="comment-reaction-response"
        )


class SyncCommentFromWebhook(Command):
    """Sync Comment from Webhook - Process comment events from PM services"""

    class Meta:
        key = "sync-comment-from-webhook"
        resources = ("comment",)
        tags = ["webhook", "sync", "comment"]
        auth_required = True
        description = "Sync comment from webhook event"
        policy_required = False
        internal = True
        new_resource = True

    Data = datadef.SyncCommentFromWebhookPayload

    async def _process(self, agg, stm, payload):
        """Process comment sync from webhook"""

        action = payload.action
        provider = payload.provider
        external_id = payload.external_id
        external_data = payload.external_data
        target_id = payload.target_id
        target_type = payload.target_type

        logger.info(f"[WebhookCommand] Syncing comment: {action} from {provider}")
        logger.info(f"[WebhookCommand]   External ID: {external_id}")
        logger.info(f"[WebhookCommand]   Target: {target_type}/{target_id}")

        try:
            if action == "create":
                result = await self._handle_create(
                    agg, stm, external_data, target_id, target_type, provider
                )
            else:
                result = {"status": "unknown_action", "action": action}

            yield agg.create_response(result, _type="webhook-response")

        except Exception as e:
            logger.error(f"[WebhookCommand] Error: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="webhook-response"
            )

    async def _handle_create(
        self, agg, stm, external_data, target_id, target_type, provider
    ):
        """Handle comment creation from webhook"""

        external_comment_id = external_data.get("id")
        body = external_data.get("body")
        parent_id = external_data.get("parentId")

        existing_integ = await stm.find_one(
            "comment_integration",
            where={"external_id": external_comment_id, "provider": provider},
        )

        if existing_integ:
            logger.info(f"Comment {external_comment_id} already exists")
            return {"status": "skipped", "reason": "already_exists"}

        integration_table = f"{target_type}_integration"
        if target_type == "issue":
            integration_table = "ticket_integration"

        target_integ = await stm.find_one(
            integration_table, where={"external_id": target_id, "provider": provider}
        )

        if not target_integ:
            logger.warning(f"No {target_type} found for external ID: {target_id}")
            return {"status": "skipped", "reason": f"no_{target_type}_mapping"}

        local_target_id = getattr(
            target_integ, f"{target_type}_id", target_integ.ticket_id
        )
        ticket_target = await stm.find_one("ticket", where={"_id": local_target_id})
        logger.info(f"ticket_target: {ticket_target}")

        comment_payload = datadef.CreateCommentPayload(content=body)
        comment_result = serialize_mapping(comment_payload)
        comment_result["parent_id"] = parent_id if parent_id else None
        comment_result["depth"] = 1 if parent_id else 0
        comment_result["resource"] = "ticket" if target_type == "issue" else target_type
        comment_result["resource_id"] = str(local_target_id)
        comment_result["source"] = "system"
        comment_result["organization_id"] = str(ticket_target.organization_id)

        new_comment = await agg.create_comment_from_webhook(data=comment_result)
        logger.info(f"agg: {agg.get_aggroot()}")

        integration_payload = datadef.CreateCommentIntegrationPayload(
            provider=provider,
            external_id=external_comment_id,
            external_url=external_data.get("issue", {}).get("url"),
            comment_id=new_comment._id,
            source="system",
        )
        await agg.create_comment_integration(data=integration_payload)
        return {
            "status": "created",
            "comment_id": str(new_comment._id),
            "external_id": external_comment_id,
        }


class SyncCommentFromWebhookChange(Command):
    """Sync Comment from Webhook - Process comment events from PM services"""

    class Meta:
        key = "sync-comment-from-webhook-change"
        resources = ("comment",)
        tags = ["webhook", "sync", "comment"]
        auth_required = True
        description = "Sync comment from webhook event"
        policy_required = False
        internal = True
        new_resource = False

    Data = datadef.SyncCommentFromWebhookPayload

    async def _process(self, agg, stm, payload):
        """Process comment sync from webhook change"""

        action = payload.action
        provider = payload.provider
        external_id = payload.external_id
        external_data = payload.external_data
        target_id = payload.target_id
        target_type = payload.target_type

        logger.info(f"[WebhookCommand] Syncing comment: {action} from {provider}")
        logger.info(f"[WebhookCommand]   External ID: {external_id}")
        logger.info(f"[WebhookCommand]   Target: {target_type}/{target_id}")

        try:
            if action == "update":
                result = await self._handle_update(
                    agg, stm, external_data, external_id, provider
                )
            elif action == "delete" or action == "remove":
                result = await self._handle_delete(agg, stm, external_id, provider)
            else:
                result = {"status": "unknown_action", "action": action}

            yield agg.create_response(result, _type="webhook-response")
        except Exception as e:
            logger.error(f"[WebhookCommand] Error: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="webhook-response"
            )

    async def _handle_update(self, agg, stm, external_data, external_id, provider):
        """Handle comment update using aggregate pattern"""

        logger.info("[WebhookCommand] Updating comment")
        logger.info(f"[WebhookCommand]   External ID: {external_id}")
        logger.info(f"[WebhookCommand]   New content: {external_data.get('body')}")

        integration = await stm.find_one(
            "comment_integration",
            where={"external_id": external_id, "provider": provider},
        )

        if not integration:
            return {"status": "skipped", "reason": "no_comment_mapping"}

        if integration.source == "user":
            logger.info("[WebhookCommand] Skipping update for user-created comment")
            return {
                "status": "skipped",
                "reason": "only user can update their comments",
            }

        comment_id_to_update = integration.comment_id
        logger.info(f"[WebhookCommand] Found comment to update: {comment_id_to_update}")

        update_payload = datadef.UpdateCommentPayload(content=external_data.get("body"))
        await agg.update_comment(data=update_payload)

        await agg.update_comment_integration(
            data=datadef.UpdateCommentIntegrationPayload(
                provider=provider,
                external_id=external_id,
                external_url=external_data.get("issue", {}).get("url"),
            )
        )

    async def _handle_delete(self, agg, stm, external_id, provider):
        """Handle comment deletion using aggregate actions"""

        integration = await stm.find_one(
            "comment_integration",
            where={"external_id": external_id, "provider": provider},
        )

        if not integration:
            return {"status": "skipped", "reason": "no_comment_mapping"}
        if integration.source == "user":
            logger.info("[WebhookCommand] Skipping delete for user-created comment")
            return {
                "status": "skipped",
                "reason": "only user can delete their comments",
            }

        await agg.delete_comment()

        await agg.remove_comment_integration(
            data=datadef.RemoveCommentIntegrationPayload(
                provider=provider,
                external_id=external_id,
                comment_id=integration.comment_id,
            )
        )


### command for document project


class UploadProjectDocument(Command):
    """Upload project document"""

    class Meta:
        key = "upload-project-document"
        resources = ("project",)
        tags = ["project", "document"]
        auth_required = True
        description = "Upload project document"
        policy_required = False

    Data = datadef.UploadProjectDocumentPayload

    async def _process(self, agg, stm, payload):
        """Upload project document"""
        result = await agg.upload_project_document(data=payload)
        yield agg.create_response(
            serialize_mapping(result), _type="project-document-response"
        )


class UpdateProjectDocument(Command):
    """Update status of project document"""

    class Meta:
        key = "update-project-document"
        resources = ("project",)
        tags = ["project", "document", "status"]
        auth_required = True
        description = "Update status of project document"
        policy_required = False

    Data = datadef.UpdateProjectDocumentPayload

    async def _process(self, agg, stm, payload):
        """Update status of project document"""
        await agg.update_status_project_document(data=payload)
        yield agg.create_response(
            {"status": "success"}, _type="project-document-response"
        )


class AddParticipanToDocument(Command):
    """Add participant to document"""

    class Meta:
        key = "add-participant-to-document"
        resources = ("project",)
        tags = ["project", "document", "participant"]
        auth_required = True
        description = "Add participant to document"
        policy_required = False

    Data = datadef.AddParticipantToDocumentPayload

    async def _process(self, agg, stm, payload):
        """Add participant to document"""
        await agg.add_participant_to_document(data=payload)
        yield agg.create_response(
            {"status": "success"}, _type="project-document-response"
        )


class UploadDocument(Command):
    """Upload Global Document - Upload a document at organization level"""

    class Meta:
        key = "upload-document"
        resources = ("document",)
        tags = ["document", "upload"]
        auth_required = True
        description = "Upload a global organization document"
        new_resource = True
        policy_required = False

    Data = datadef.UploadDocumentPayload

    async def _process(self, agg, stm, payload):
        """Upload global organization document"""
        result = await agg.upload_document(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateDocument(Command):
    """Update Document - Update global document information"""

    class Meta:
        key = "update-document"
        resources = ("document",)
        tags = ["document", "update"]
        auth_required = True
        description = "Update global document information"
        policy_required = False

    Data = datadef.UpdateDocumentPayload

    async def _process(self, agg, stm, payload):
        """Update global document"""
        result = await agg.update_document(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class DeleteDocument(Command):
    """Delete Document - Delete a global organization document"""

    class Meta:
        key = "delete-document"
        resources = ("document",)
        tags = ["document", "delete"]
        auth_required = True
        description = "Delete a global organization document"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Delete global document"""
        await agg.delete_document()


class AddParticipantToGlobalDocument(Command):
    """Add Participant to Global Document - Add participant(s) to organization document"""

    class Meta:
        key = "add-participant-to-global-document"
        resources = ("document",)
        tags = ["document", "participant", "add"]
        auth_required = True
        description = "Add participant to global organization document"
        policy_required = False

    Data = datadef.AddParticipantToGlobalDocumentPayload

    async def _process(self, agg, stm, payload):
        """Add participant to global document"""
        await agg.add_participant_to_global_document(data=payload)

        yield agg.create_response(
            {"status": "success"}, _type="document-participant-response"
        )
