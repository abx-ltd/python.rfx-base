from fluvius.data import serialize_mapping

from .domain import RFXDiscussDomain
from . import datadef, utils, logger, config

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
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        mentions = utils.extract_mentions(payload.content)
        logger.info(f"Extracted mentions: {mentions}")
        if mentions:
            unique_user_ids = {mention["user_id"] for mention in mentions}
            users_info = await utils.get_mentioned_users(stm, list(unique_user_ids))
            message_content = f"{profile.name__given} mentioned you in a comment."
            message_subject = "Mention In Comment"

            if config.MESSAGE_ENABLED:
                context = agg.get_context()
                service_proxy = context.service_proxy
                await service_proxy.msg_client.send(
                    f"{config.MESSAGE_NAMESPACE}:send-message",
                    command="send-message",
                    resource="message",
                    payload={
                        "recipients": [str(user_id["id"]) for user_id in users_info],
                        "subject": message_subject,
                        "message_type": "NOTIFICATION",
                        "priority": "MEDIUM",
                        "content": message_content,
                        "content_type": "TEXT",
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(context.profile_id),
                            "profile_id": str(context.profile_id),
                            "organization_id": str(context.organization_id),
                            "realm": context.realm,
                        }
                    },
                )

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
        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        mentions = utils.extract_mentions(payload.content)
        if mentions:
            unique_user_ids = {mentions["user_id"] for mentions in mentions}
            users_info = await utils.get_mentioned_users(stm, list(unique_user_ids))
            message_content = f"{profile.name__given} mentioned you in a comment."
            message_subject = "Mention In Comment"

            if config.MESSAGE_ENABLED:
                context = agg.get_context()
                service_proxy = context.service_proxy
                await service_proxy.msg_client.send(
                    f"{config.MESSAGE_NAMESPACE}:send-message",
                    command="send-message",
                    resource="message",
                    payload={
                        "recipients": [str(user_id["id"]) for user_id in users_info],
                        "subject": message_subject,
                        "message_type": "NOTIFICATION",
                        "priority": "MEDIUM",
                        "content": message_content,
                        "content_type": "TEXT",
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(context.profile_id),
                            "profile_id": str(context.profile_id),
                            "organization_id": str(context.organization_id),
                            "realm": context.realm,
                        }
                    },
                )
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
        mentions = utils.extract_mentions(payload.content)
        if mentions:
            unique_user_ids = {mentions["user_id"] for mentions in mentions}
            users_info = await utils.get_mentioned_users(stm, list(unique_user_ids))
            profile_id = agg.get_context().profile_id
            profile = await stm.get_profile(profile_id)
            message_content = f"{profile.name__given} mentioned you in a comment."
            message_subject = "Mention In Comment"

            if config.MESSAGE_ENABLED:
                context = agg.get_context()
                service_proxy = context.service_proxy
                await service_proxy.msg_client.send(
                    f"{config.MESSAGE_NAMESPACE}:send-message",
                    command="send-message",
                    resource="message",
                    payload={
                        "recipients": [str(user_id["id"]) for user_id in users_info],
                        "subject": message_subject,
                        "message_type": "NOTIFICATION",
                        "priority": "MEDIUM",
                        "content": message_content,
                        "content_type": "TEXT",
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(context.profile_id),
                            "profile_id": str(context.profile_id),
                            "organization_id": str(context.organization_id),
                            "realm": context.realm,
                        }
                    },
                )

        result = await agg.reply_to_comment(data=payload)
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


class AddReaction(Command):
    """Add Reaction to Comment"""

    class Meta:
        key = "add-reaction"
        resources = ("comment",)
        tags = ["comment", "reaction", "add"]
        auth_required = True
        description = "Add reaction to comment"
        policy_required = False

    Data = datadef.AddReactionPayload

    async def _process(self, agg, stm, payload):
        """Add reaction to comment"""
        comment = agg.get_aggroot()
        if not comment:
            raise ValueError(f"Comment not found: {agg.get_aggroot().identifier}")
        await agg.add_reaction(data=payload)
        yield agg.create_response(
            {"status": "success"}, _type="comment-reaction-response"
        )


class RemoveReaction(Command):
    """Remove Reaction from Comment"""

    class Meta:
        key = "remove-reaction"
        resources = ("comment",)
        tags = ["comment", "reaction", "remove"]
        auth_required = True
        description = "Remove reaction from comment"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Remove reaction from comment"""
        await agg.remove_reaction()
        yield agg.create_response(
            {"status": "success"}, _type="comment-reaction-response"
        )


class FlagComment(Command):
    """Flag Comment - Flags a comment as inappropriate"""

    class Meta:
        key = "flag-comment"
        resources = ("comment",)
        tags = ["comment", "flag"]
        auth_required = True
        description = "Flag a comment as inappropriate"
        policy_required = False

    Data = datadef.FlagCommentPayload

    async def _process(self, agg, stm, payload):
        """Flag comment"""
        result = await agg.flag_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="flag-response")


class ResolveFlag(Command):
    """Resolve Flag - Resolves a flag on a comment"""

    class Meta:
        key = "resolve-flag"
        resources = ("comment",)
        tags = ["comment", "flag", "resolve"]
        auth_required = True
        description = "Resolve a flag on a comment"
        policy_required = False

    Data = datadef.ResolveFlagPayload

    async def _process(self, agg, stm, payload):
        """Resolve flag"""
        result = await agg.resolve_flag(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="flag-response")
