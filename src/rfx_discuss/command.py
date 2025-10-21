from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXDiscussDomain
from . import datadef, config
from .types import ActivityAction

processor = RFXDiscussDomain.command_processor
Command = RFXDiscussDomain.Command


# ---------- Inquiry (Ticket Context) ----------




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
        # yield agg.create_message(
        #         "update-comment-integration-message",
        #         data={
        #             "command": "update-comment-integration",
        #             "comment": serialize_mapping(updated_comment),
        #             "comment_id": str(agg.get_aggroot().identifier),
        #             "payload": {
        #                 "provider": "linear",
        #                 "external_id": str(agg.get_aggroot().identifier),
        #             },
        #             "context": {
        #                 "user_id": agg.get_context().user_id,
        #                 "profile_id": agg.get_context().profile_id,
        #                 "organization_id": agg.get_context().organization_id,
        #                 "realm": agg.get_context().realm,
        #             }
        #         }
        #     )


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
        
        
        # if payload.sync_linear:
        #     yield agg.create_message(
        #         "remove-comment-integration-message",
        #         data={
        #             "command": "remove-comment-integration",
        #             "comment_id": str(agg.get_aggroot().identifier),
        #             "payload": {
        #                 "provider": "linear",
        #                 "external_id": str(agg.get_aggroot().identifier),
        #             },
        #             "context": {
        #                 "user_id": agg.get_context().user_id,
        #                 "profile_id": agg.get_context().profile_id,
        #                 "organization_id": agg.get_context().organization_id,
        #                 "realm": agg.get_context().realm,
        #             }
        #         }
        #     )
        
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
        
        # yield agg.create_message(
        #         "create-comment-integration-message",
        #         data={
        #             "command": "create-comment-integration",
        #             "comment": serialize_mapping(result),
        #             "comment_id": str(result._id),
        #             "ticket_id": str(agg.get_aggroot().identifier), 
        #             "payload": {
        #                 "provider": "linear",
        #                 "external_id": str(result._id),
        #             },
        #             "context": {
        #                 "user_id": agg.get_context().user_id,
        #                 "profile_id": agg.get_context().profile_id,
        #                 "organization_id": agg.get_context().organization_id,
        #                 "realm": agg.get_context().realm,
        #             }
        #         }
        #     )

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
        # yield agg.create_message(
        #     "sync-ticket-to-linear-message",
        #     data={
        #         "command": "sync-ticket-integration",
        #         "ticket": serialize_mapping(ticket),
        #         "ticket_id": str(agg.get_aggroot().identifier),
        #         "project_id": str(project_id),
        #         "context": {
        #             "user_id": agg.get_context().user_id,
        #             "profile_id": agg.get_context().profile_id,
        #             "organization_id": agg.get_context().organization_id,
        #             "realm": agg.get_context().realm,
        #         }
        #     }
        # )
  

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
        

        

