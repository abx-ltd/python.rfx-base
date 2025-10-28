from fluvius.data import serialize_mapping

from .domain import RFXDiscussDomain
from . import datadef


processor = RFXDiscussDomain.command_processor
Command = RFXDiscussDomain.Command


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
        resources = ("comment",)
        tags = ["comment"]
        auth_required = True
        description = "Create a new comment"
        policy_required = False
        new_resource = True

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
        await stm.find_one("comment", where=dict(_id=agg.get_aggroot().identifier))


class DeleteComment(Command):
    """Delete Comment - Deletes a comment"""

    class Meta:
        key = "delete-comment"
        resources = ("comment",)
        tags = ["comment", "delete"]
        auth_required = True
        description = "Delete a comment"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Delete comment"""
        await agg.delete_comment()


class ReplyToComment(Command):
    """Reply to Comment - Replies to a comment"""

    class Meta:
        key = "reply-to-comment"
        resources = ("comment",)
        tags = ["comment", "reply"]
        auth_required = True
        description = "Reply to a comment"
        policy_required = False

    Data = datadef.ReplyToCommentPayload

    async def _process(self, agg, stm, payload):
        """Reply to comment"""
        result = await agg.reply_to_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")
