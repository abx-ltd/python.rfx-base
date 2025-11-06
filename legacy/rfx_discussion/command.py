from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXDiscussionDomain
from . import datadef, config
from .types import ActivityAction

from rfx_integration.pm_service import PMService
from rfx_integration.pm_service.base import CreateTicketPayload
from rfx_integration.pm_service.base import UpdateTicketPayload as PMUpdatePayload
processor = RFXDiscussionDomain.command_processor
Command = RFXDiscussionDomain.Command


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
            }
        )
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
            }
        )
        ticket_id = result._id
        
        logger.info(f"PROJECT_MANAGEMENT_INTEGRATION_ENABLED: {config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED}, sync_linear: {payload.sync_linear}")
        logger.info(f"Payload: {payload}")
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and payload.sync_linear:
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
                        team_id=str(config.LINEAR_TEAM_ID),
                    )
                    
                    pm_response = await pm_service.create_ticket(pm_payload)
                    
                    logger.info(f"pm_responese {pm_response}")
                    
                  
                    integration_result = await agg.create_ticket_integration(
                        data=datadef.CreateTicketIntegrationPayload(
                            provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                            external_id=pm_response.external_id,
                            external_url=pm_response.url
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

        ticket = await stm.find_one("ticket", where=dict(_id=agg.get_aggroot().identifier))

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a ticket {ticket.title}",
            msglabel="update ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED and payload.sync_linear:
            try:
                # Find existing integration
                integration = await stm.find_one("ticket-integration", where=dict(
                    ticket_id=agg.get_aggroot().identifier,
                    provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                ))
                
                if not integration:
                    logger.warning("No integration found for this ticket, skipping sync")
                else:
                    
                    
                    logger.info(f"Syncing update to {config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER}")
                    logger.info(f"External ID: {integration.external_id}")
                    
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        
                        # Build update payload - only include changed fields
                        pm_payload = PMUpdatePayload(
                            external_id=integration.external_id,
                            title=payload.title if payload.title else None,
                            description=payload.description if payload.description else None,
                            status_id=str(payload.status) if hasattr(payload, 'status') and payload.status else None,
                            assignee_id=str(payload.assignee) if hasattr(payload, 'assignee') and payload.assignee else None,
                            priority=payload.priority if hasattr(payload, 'priority') and payload.priority else None,
                        )
                        
                        pm_response = await pm_service.update_ticket(pm_payload)
                        logger.info(f"PM Response: {pm_response}")
                        
                        logger.info(f"✓ Updated in {config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER}")
                        logger.info(f"  External ID: {integration.external_id}")
                        logger.info(f"  Updated: {pm_response.updated}")
                        
                        # ✅ Update integration metadata
                        integration_update_result = await agg.update_ticket_integration(
                            data=datadef.UpdateTicketIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id,
                                external_url=pm_response.external_url
                            )
                        )
                        
                        logger.info(f"✓ Updated integration metadata")
                        
            except Exception as e:
                logger.error(f"✗ Failed to sync update to PM service: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        ticket_update = await stm.find_one("ticket", where=dict(_id=agg.get_aggroot().identifier))
        
        
        yield agg.create_response(serialize_mapping(ticket_update), _type="ticket-response")


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

        ticket = await stm.find_one("ticket", where=dict(_id=agg.get_aggroot().identifier))

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a ticket {ticket.title}",
            msglabel="remove ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            try:
                # Find integration
                integration = await stm.find_one("ticket-integration", where=dict(
                    ticket_id=agg.get_aggroot().identifier,
                    provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                ))
                
                if integration:
                    from rfx_integration.pm_service import PMService
                    
                    logger.info(f"Removing ticket from {config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER}")
                    logger.info(f"External ID: {integration.external_id}")
                    
                    async with PMService.init_client(
                        provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER
                    ) as pm_service:
                        
                        # Delete from PM service
                        success = await pm_service.delete_ticket(
                            external_id=integration.external_id,
                            permanently=True  # or False for soft delete
                        )
                        
                        if success:
                            logger.info(f"✓ Deleted from {config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER}")
                        else:
                            logger.warning(f"Failed to delete from {config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER}")
                        
                  
                        await agg.remove_ticket_integration(
                            data=datadef.RemoveTicketIntegrationPayload(
                                provider=config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
                                external_id=integration.external_id
                            )
                        )
                        
                        logger.info(f"✓ Removed integration record")
                else:
                    logger.info("No integration found, skipping PM service deletion")
                    
            except Exception as e:
                logger.error(f"✗ Failed to remove from PM service: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        

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
            }
        )

        await agg.assign_member_to_ticket(data=payload)


class RemoveMemberFromTicket(Command):
    """Remove Member from Ticket - Removes a member from ticket"""

    class Meta:
        key = "remove-member"
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
            }
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
            }
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
            }
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
        yield agg.create_response(serialize_mapping(result), _type="ticket-type-response")


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
            }
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
            }
        )

        await agg.remove_ticket_tag(payload.tag_id)


# ---------- Comment Context ----------


class CreateComment(Command):
    """Create Comment - Creates a new comment"""

    class Meta:
        key = "create-comment"
        resources = ("comment",)
        tags = ["comment"]
        auth_required = True
        description = "Create a new comment"
        new_resource = True
        internal = True

    Data = datadef.CreateCommentPayload

    async def _process(self, agg, stm, payload):
        """Create comment"""
        result = await agg.create_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


class UpdateComment(Command):
    """Update Comment - Updates a comment"""

    class Meta:
        key = "update-comment"
        resources = ("comment",)
        tags = ["comment", "update"]
        auth_required = True
        description = "Update a comment"
        policy_required = False

    Data = datadef.UpdateCommentPayload

    async def _process(self, agg, stm, payload):
        """Update comment"""
        await agg.update_comment(data=payload)
        updated_comment = await stm.find_one("comment", where=dict(_id=agg.get_aggroot().identifier))
        yield agg.create_message(
                "update-comment-integration-message",
                data={
                    "command": "update-comment-integration",
                    "comment": serialize_mapping(updated_comment),
                    "comment_id": str(agg.get_aggroot().identifier),
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


class DeleteComment(Command):
    """Delete Comment - Deletes a comment"""

    class Meta:
        key = "delete-comment"
        resources = ("comment",)
        tags = ["comment", "delete"]
        auth_required = True
        description = "Delete a comment"
        policy_required = False
        
        
    Data = datadef.DeleteCommentPayload

    async def _process(self, agg, stm, payload):
        """Delete comment"""
        
        
        if payload.sync_linear:
            yield agg.create_message(
                "remove-comment-integration-message",
                data={
                    "command": "remove-comment-integration",
                    "comment_id": str(agg.get_aggroot().identifier),
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
        
        await agg.delete_comment()
        


class ReplyToComment(Command):
    """Reply to Comment - Replies to a comment"""

    class Meta:
        key = "reply-to-comment"
        resources = ("comment",)
        tags = ["comment", "reply"]
        auth_required = True
        description = "Reply to a comment"

    Data = datadef.ReplyToCommentPayload

    async def _process(self, agg, stm, payload):
        """Reply to comment"""
        result = await agg.reply_to_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


# ------------ Ticket Comment (Ticket Context) ------------
class CreateTicketComment(Command):
    """Create Ticket Comment - Creates a new comment for a ticket"""

    class Meta:
        key = "create-ticket-comment"
        resources = ("ticket",)
        tags = ["ticket", "comment"]
        auth_required = True
        description = "Create a new comment for a ticket"
        policy_required = True

    Data = datadef.CreateTicketCommentPayload

    async def _process(self, agg, stm, payload):
        """Create ticket comment"""
        result = await agg.create_ticket_comment(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a comment",
            msglabel="create comment",
            msgtype=ActivityType.USER_ACTION,
            data={
                "comment_id": result._id,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        
        yield agg.create_message(
                "create-comment-integration-message",
                data={
                    "command": "create-comment-integration",
                    "comment": serialize_mapping(result),
                    "comment_id": str(result._id),
                    "ticket_id": str(agg.get_aggroot().identifier), 
                    "payload": {
                        "provider": "linear",
                        "external_id": str(result._id),
                    },
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )

        yield agg.create_response(serialize_mapping(result), _type="comment-response")


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
        yield agg.create_response(serialize_mapping(status_key), _type="status-key-response")


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
        yield agg.create_response(serialize_mapping(status_transition), _type="status-transition-response")

# ------------ Linear Integration (Ticket Context) ------------
class SyncTicketToLinear(Command):
    """Sync Ticket to Linear - Sync a ticket to Linear"""

    class Meta:
        key = "sync-ticket-to-linear"
        resources = ("ticket",)
        tags = ["ticket", "linear"]
        auth_required = True
        description = "Sync a ticket to Linear"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Sync a ticket to Linear"""
        ticket = agg.get_rootobj()
        project_id = await stm.get_project_id_by_ticket_id(agg.get_aggroot().identifier)
        logger.info(f"[Linear] Project ID: {project_id}")
        yield agg.create_message(
            "sync-ticket-to-linear-message",
            data={
                "command": "sync-ticket-integration",
                "ticket": serialize_mapping(ticket),
                "ticket_id": str(agg.get_aggroot().identifier),
                "project_id": str(project_id),
                "context": {
                    "user_id": agg.get_context().user_id,
                    "profile_id": agg.get_context().profile_id,
                    "organization_id": agg.get_context().organization_id,
                    "realm": agg.get_context().realm,
                }
            }
        )
        
class SyncAllTicketsToLinear(Command):
    """Sync All Tickets to Linear - Sync all tickets to Linear"""

    class Meta:
        key = "sync-all-tickets-to-linear"
        resources = ("ticket",)
        tags = ["ticket", "linear"]
        auth_required = True
        description = "Sync all tickets to Linear"
        policy_required = False
        new_resource = True
    Data = datadef.SyncAllTicketsToLinearPayload
    async def _process(self, agg, stm, payload):
        """Sync all tickets to Linear"""
        project_id = payload.project_id
        logger.info(f"[Linear] Syncing all tickets for Project ID: {project_id}")
        ticket_id_records = await stm.get_ticket_ids_by_project_id(project_id)
        if not ticket_id_records:
            logger.info(f"[Linear] No tickets found for Project ID: {project_id}. Sync finished.")
            return
        ticket_ids = [record.ticket_id for record in ticket_id_records]
        tickets = await stm.get_tickets_by_ids(ticket_ids)
        for ticket in tickets:
            yield agg.create_message(
                "sync-ticket-to-linear-message",
                data={
                    "command": "sync-ticket-integration",
                    "ticket": serialize_mapping(ticket),
                    "ticket_id": str(ticket._id),
                    "project_id": str(project_id),
                    "context": {
                        "user_id": agg.get_context().user_id,
                        "profile_id": agg.get_context().profile_id,
                        "organization_id": agg.get_context().organization_id,
                        "realm": agg.get_context().realm,
                    }
                }
            )       
#--------------- Ticket Integration------------

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
        
        
class SyncTicketIntegration(Command):
    """Sync Ticket Integration - Sync a ticket integration"""

    class Meta:
        key = "sync-ticket-integration"
        resources = ("ticket",)
        tags = ["ticket", "integration"]
        auth_required = True
        description = "Sync a ticket integration"
        policy_required = False
        internal = True

    Data = datadef.SyncTicketIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Sync a ticket integration"""
        await agg.sync_ticket_integration(data=payload)


#--------------- Comment Integration Commands ---------------
class CreateCommentIntegration(Command):
    """Create Comment Integration"""
    
    class Meta:
        key = "create-comment-integration"
        resources = ("comment",)
        tags = ["comment", "integration"]
        auth_required = True
        description = "Create a comment integration"
        policy_required = False
        internal = True
        
    Data = datadef.CreateCommentIntegrationPayload
    
    async def _process(self, agg, stm, payload):
        """Create a comment integration"""
        result = await agg.create_comment_integration(data=payload)


class UpdateCommentIntegration(Command):
    """Update Comment Integration - Update a comment integration"""

    class Meta:
        key = "update-comment-integration"
        resources = ("comment",)
        tags = ["comment", "integration"]
        auth_required = True
        description = "Update a comment integration"
        policy_required = False
        internal = True

    Data = datadef.UpdateCommentIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Update a comment integration"""
        result = await agg.update_comment_integration(data=payload)
        


class RemoveCommentIntegration(Command):
    """Remove Comment Integration - Remove a comment integration"""

    class Meta:
        key = "remove-comment-integration"
        resources = ("comment",)
        tags = ["comment", "integration"]
        auth_required = True
        description = "Remove a comment integration"
        policy_required = False
        internal = False
        new_resource = True

    Data = datadef.RemoveCommentIntegrationPayload

    async def _process(self, agg, stm, payload):
        """Remove a comment integration"""
        result = await agg.remove_comment_integration(data=payload)
        

        

