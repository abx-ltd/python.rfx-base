# Command definitions
# Define command classes here
from datetime import datetime, timedelta
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.data.exceptions import ItemNotFoundError
from fluvius.domain.activity import ActivityType
from fluvius.error import BadRequestError
from .domain import RFX2DMessageDomain
from .types import DirectionTypeEnum, ProcessingModeEnum
from typing import Any, Dict

from . import datadef, config, logger, helper

Command = RFX2DMessageDomain.Command

# =======================================
# MAILBOX METHODS
# =======================================

class CreateMailbox(Command):
    Data = datadef.CreateMailboxPayload

    class Meta:
        key = "create-mailbox"
        resources = ("mailbox",)
        resource_init = True
        tags = ["mailbox", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        payload = serialize_mapping(payload)

        mailbox_result = await agg.create_mailbox(data=payload, profile_id=profile_id)

        yield agg.create_response(
            serialize_mapping(mailbox_result),
            _type="message-response"
        )

class RemoveMailbox(Command):
    class Meta:
        key = "remove-mailbox"
        resources = ("mailbox",)
        tags = ["mailbox", "remove"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        mailbox_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        result = await agg.remove_mailbox(mailbox_id=mailbox_id, profile_id=profile_id)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class AddMemberToMailbox(Command):
    Data = datadef.AddMemberToMailboxPayload

    class Meta:
        key = "add-member-to-mailbox"
        resources = ("mailbox",)
        tags = ["mailbox", "member", "add"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        mailbox_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id
        payload = serialize_mapping(payload)

        await agg.add_member_to_mailbox(mailbox_id=mailbox_id, 
                                        profile_id=profile_id, 
                                        member_ids=payload.pop("profile_ids", []),
                                        assign_all_message=payload.pop("assign_all_message", False)
                                        )

class RemoveMemberFromMailbox(Command):
    Data = datadef.RemoveMemberFromMailboxPayload

    class Meta:
        key = "remove-member-from-mailbox"
        resources = ("mailbox",)
        tags = ["mailbox", "member", "remove"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        mailbox_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id
        payload = serialize_mapping(payload)

        await agg.remove_member_from_mailbox(mailbox_id=mailbox_id, 
                                            profile_id=profile_id, 
                                            member_ids=payload.get("profile_ids", [])
                                            )

# =======================================
# MESSAGE METHOD
# =======================================

class SendMessageToMailbox(Command):
    """
    Send a notification message to recipients in a mailbox.

    Supports both template-based and direct content messages.
    """

    Data = datadef.SendMessageToMailboxPayload

    class Meta:
        key = "send-message-to-mailbox"
        resource_init = True
        resources = ("message",)
        tags = ["message", "mailbox"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)
        profile_id = agg.get_context().profile_id
        mailbox_id = message_payload.pop("mailbox_id")
        send_all = message_payload.pop("send_all", True)
        recipients = message_payload.pop("recipients", [])
        send_all = message_payload.get("send_all", True)

        # 0. Check profile is owner or contributor of the mailbox
        await agg.check_owner_contributor_mailbox(profile_id=profile_id, mailbox_id=mailbox_id)

        # 1. Get recipients
        members = await stm.find_all("mailbox_member", where={"mailbox_id": mailbox_id})
        if send_all:
            # Get all members from mailbox
            recipients = [m.member_id for m in members if m.member_id != profile_id]  # exclude sender if in members
        else:
            recipients_input = recipients or []
            recipients = []
            for r in recipients_input:
                if r in [m.member_id for m in members]:
                    recipients.append(r)

        if not recipients:
            raise BadRequestError("D00.500", "No recipients specified")

        # 2. Create message record
        message_result = await agg.generate_message(
            data=message_payload, mailbox_id=mailbox_id
        )
        message_id = message_result._id

        # 3. Add sender to message_sender with mailbox as box
        await agg.add_sender(message_id=message_id, sender_id=profile_id)

        # 4. Add message to message_recipient
        await agg.add_message_recipient(message_id=message_id, mailbox_id=mailbox_id)

        # 5. Assign message_mailbox_state for each recipient
        for recipient in recipients:
            await agg.assign_message(message_id=message_id, mailbox_id=mailbox_id, assignee_profile_id=recipient)

        # 6. Determine processing mode and get client
        processing_mode, client = await helper.get_processing_mode_and_client(
            agg, message_payload
        )

        # 7. Process message content
        message = await helper.determine_and_process_message(
            agg, message_id, message_payload, processing_mode
        )

        user_ids = await stm.get_user_ids_from_profile_ids(recipients)

        # 8. Notify recipients
        helper.notify_recipients(
            client,
            recipients,
            user_ids,
            "message",
            message_id,
            message,
            processing_mode,
        )

        # 9. Create response
        response_data = serialize_mapping(message_result)

        yield agg.create_response(
            response_data,
            _type="message-response",
        )

# class RemoveMessage(Command):
#     """
#     Send a notification message to recipients in a mailbox.

#     Supports both template-based and direct content messages.
#     """

#     Data = datadef.RemoveMessagePayload

#     class Meta:
#         key = "remove-message-from-mailbox"
#         resources = ("message",)
#         tags = ["message", "mailbox"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         message_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

class AssignMessage(Command):
    """Assign handling of a message for a mailbox."""

    Data = datadef.AssignMessagePayload

    class Meta:
        key = "assign-message"
        resources = ("message",)
        tags = ["message", "assign"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        mailbox_id=payload.mailbox_id
        assignee_profile_id=payload.assignee_profile_id

        result = await agg.assign_message(
            message_id=message_id,
            mailbox_id=mailbox_id,
            assignee_profile_id=assignee_profile_id,
        )

        message = await agg.get_message_mailbox(message_id=message_id, mailbox_id=mailbox_id)

        processing_mode = ProcessingModeEnum.SYNC

        context = agg.get_context()
        client = context.service_proxy.mqtt_client

        recipients = [assignee_profile_id]
        user_ids = await stm.get_user_ids_from_profile_ids(recipients)
        
        message = await agg.map_message_to_dict(message)
        
        # Notify recipients
        helper.notify_recipients(
            client,
            recipients,
            user_ids,
            "message",
            message_id,
            message,
            processing_mode,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Assigned message {message_id} to profile {payload.assignee_profile_id}",
            msglabel="assign-message",
            msgtype=ActivityType.USER_ACTION,
            data={
                "mailbox_id": str(payload.mailbox_id),
                "assignee_profile_id": str(payload.assignee_profile_id),
            },
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class SetMessageStatus(Command):
    """Update canonical message status."""

    Data = datadef.SetMessageStatusPayload

    class Meta:
        key = "set-message-status"
        resources = ("message",)
        tags = ["message", "status"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        result = await agg.set_message_status(
            message_id=message_id,
            message_status=payload.message_status,
            mailbox_id=payload.mailbox_id,
            profile_id=agg.get_context().profile_id,
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class MoveMessage(Command):
    """Move a message into a folder for this mailbox."""

    Data = datadef.MoveMessagePayload

    class Meta:
        key = "move-message"
        resources = ("message",)
        tags = ["message", "move"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        result = await agg.move_message(
            message_id=message_id,
            mailbox_id=payload.mailbox_id,
            folder=payload.folder,
            profile_id=profile_id
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class SetMessageStar(Command):
    """Toggle star state for a mailbox-specific message view."""

    Data = datadef.SetMessageStarPayload

    class Meta:
        key = "set-message-star"
        resources = ("message",)
        tags = ["message", "star"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        result = await agg.set_message_star(
            message_id=message_id,
            mailbox_id=payload.mailbox_id,
            starred=payload.starred,
            profile_id=profile_id,
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class SetPriority(Command):
    """Change message priority."""

    Data = datadef.SetPriorityPayload

    class Meta:
        key = "set-priority"
        resources = ("message",)
        tags = ["message", "priority"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        result = await agg.set_priority(
            message_id=message_id,
            priority=payload.priority,
            profile_id=profile_id
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class UploadAttachmentMetadata(Command):
    """Register metadata for an uploaded attachment."""

    Data = datadef.UploadAttachmentMetadataPayload

    class Meta:
        key = "upload-attachment"
        resources = ("message",)
        tags = ["message", "attachment"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        result = await agg.upload_attachment_metadata(
            message_id=message_id,
            data=payload,
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class MarkReadMessage(Command):
    Data = datadef.MarkReadMessagePayload

    class Meta:
        key = "mark-read-message"
        resources = ("message",)
        tags = ["message", "attachment"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id
        payload = serialize_mapping(payload)

        result = await agg.mark_message_is_read(
            mailbox_id=payload.pop("mailbox_id", None),
            message_id=message_id,
            profile_id=profile_id,
            is_read=payload.pop("read", True)
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

# =======================================
# TAG METHOD
# =======================================

class CreateTag(Command):
    """Create a new tag for the current user"""
    Data = datadef.CreateTagPayload

    class Meta:
        key = "create-tag"
        resource_init = True
        resources = ("tag",)
        tags = ["tag", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.create_tag(data=payload)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class UpdateTag(Command):
    """Update a tag."""

    Data = datadef.UpdateTagPayload

    class Meta:
        key = "update-tag"
        resources = ("tag",)
        tags = ["tag", "update"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.update_tag(data=payload)
        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class RemoveTag(Command):
    """Remove a tag."""

    class Meta:
        key = "remove-tag"
        resources = ("tag",)
        tags = ["tag", "remove"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        tag_id = agg.get_aggroot().identifier
        
        # await agg.remove_message_tag(tag_id=tag._id)
        await agg.remove_message_tag_from_tag(tag_id=tag_id)
        await agg.remove_tag(tag_id=tag_id)

class AddMessageTag(Command):
    """Add a message to a tag"""

    Data = datadef.AddMessageTagPayload

    class Meta:
        key = "add-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    Data = datadef.AddMessageTagPayload

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        payload = serialize_mapping(payload)
        tag_ids = payload.get("tag_ids", [])

        await agg.add_message_tag(message_id=message_id, tag_ids=tag_ids)

class RemoveMessageTag(Command):
    """Remove a message from a tag."""

    Data = datadef.RemoveMessageTagPayload

    class Meta:
        key = "remove-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        payload = serialize_mapping(payload)
        tag_ids = payload.get("tag_ids", [])

        await agg.remove_message_tag(message_id=message_id, tag_ids=tag_ids)

# =======================================
# CATEGORY METHOD
# =======================================

class CreateCategory(Command):
    Data = datadef.CreateCategoryPayload

    class Meta:
        key = "create-category"
        resources = ("category",)
        resource_init = True
        tags = ["category", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id

        result = await agg.create_category(data=payload, profile_id=profile_id)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class UpdateCategory(Command):
    Data = datadef.UpdateCategoryPayload

    class Meta:
        key = "update-category"
        resources = ("category",)
        tags = ["category", "update"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_category(data=payload)
        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class RemoveCategory(Command):

    class Meta:
        key = "remove-category"
        resources = ("category",)
        tags = ["category", "remove"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        category_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        await agg.remove_category(category_id=category_id, profile_id=profile_id)

class AddMessageCategory(Command):
    Data = datadef.AddMessageCategoryPayload

    class Meta:
        key = "add-message-category"
        resources = ("category",)
        tags = ["message", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        category_id = agg.get_aggroot().identifier

        payload = serialize_mapping(payload)
        message_ids = payload.get("message_ids", [])
        mailbox_id = payload.get("mailbox_id")

        result = await agg.add_message_to_category(mailbox_id=mailbox_id, 
                                                   category_id=category_id, 
                                                   message_ids=message_ids)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class RemoveMessageCategory(Command):

    Data = datadef.RemoveMessageCategoryPayload

    class Meta:
        key = "remove-message-category"
        resources = ("category",)
        tags = ["message", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        category_id = agg.get_aggroot().identifier
        profile_id = agg.get_context().profile_id

        payload = serialize_mapping(payload)
        message_ids = payload.get("message_ids", [])
        mailbox_id = payload.get("mailbox_id")

        result = await agg.remove_message_from_category(mailbox_id=mailbox_id, 
                                                        category_id=category_id, 
                                                        profile_id=profile_id, 
                                                        message_ids=message_ids)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

# =======================================
# ACTION METHODS
# =======================================

class RegisterAction(Command):
    """Register or update an action definition for a mailbox."""
    Data = datadef.RegisterActionPayload

    class Meta:
        key = "register-action"
        resources = ("mailbox",)
        tags = ["action", "register"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        mailbox_id = agg.get_aggroot().identifier  # Mailbox is the aggregate root

        payload = serialize_mapping(payload)

        result = await agg.register_action(
            mailbox_id=mailbox_id,
            action_data=payload,
            profile_id=profile_id
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class ExecuteAtomicAction(Command):
    """Execute an atomic action for a message."""
    Data = datadef.ExecuteAtomicActionPayload

    class Meta:
        key = "execute-atomic-action"
        resources = ("message",)
        tags = ["action", "execute", "atomic"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        message_id = agg.get_aggroot().identifier  # Message is the aggregate root

        payload = serialize_mapping(payload)

        result = await agg.execute_atomic_action(
            message_id=message_id,
            action_id=payload["action_id"],
            profile_id=profile_id,
            mailbox_id=payload["mailbox_id"]
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class SubmitFormAction(Command):
    """Submit a form action for a message."""
    Data = datadef.SubmitFormActionPayload

    class Meta:
        key = "submit-form-action"
        resources = ("message",)
        tags = ["action", "submit", "form"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        message_id = agg.get_aggroot().identifier  # Message is the aggregate root

        payload = serialize_mapping(payload)

        result = await agg.submit_form_action(
            message_id=message_id,
            action_id=payload["action_id"],
            form_data=payload["form_data"],
            profile_id=profile_id
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class CreateActionExecution(Command):
    """Execute an embedded action for a message (creates pending execution)."""
    Data = datadef.CreateActionExecutionPayload

    class Meta:
        key = "create-action-execution"
        resources = ("message",)
        tags = ["action", "execution", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        message_id = agg.get_aggroot().identifier  # Message is the aggregate root

        payload = serialize_mapping(payload)

        result = await agg.create_action_execution(
            message_id=message_id,
            action_id=payload["action_id"],
            profile_id=profile_id,
            mailbox_id=payload["mailbox_id"]
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class RecordEmbeddedActionResult(Command):
    """Record the result of an embedded action."""
    Data = datadef.RecordEmbeddedActionResultPayload

    class Meta:
        key = "record-embedded-action-result"
        resources = ("message",)
        tags = ["action", "record", "embedded"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = agg.get_context().profile_id
        message_id = agg.get_aggroot().identifier  # Message is the aggregate root

        payload = serialize_mapping(payload)

        result = await agg.record_embedded_action_result(
            message_id=message_id,
            action_id=payload["action_id"],
            execution_id=payload["execution_id"],
            callback_payload=payload["callback_payload"],
            profile_id=profile_id
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

# =======================================
# LINK METHODS
# =======================================
    
class LinkMessage(Command):
    Data = datadef.LinkMessagePayload

    class Meta:
        key = "link-related-message"
        resources = ("message",)
        tags = ["message", "related", "link"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        payload = serialize_mapping(payload)

        mailbox_id = payload["mailbox_id"]
        left_message_id = payload["left_message_id"]
        link_type = payload["link_type"]

        result = await agg.link_message(
            right_message_id=message_id, 
            left_message_id=left_message_id, 
            mailbox_id=mailbox_id, 
            link_type=link_type
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )

class UnlinkMessage(Command):
    Data = datadef.LinkMessagePayload

    class Meta:
        key = "unlink-related-message"
        resources = ("message",)
        tags = ["message", "related", "link"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        payload = serialize_mapping(payload)

        mailbox_id = payload["mailbox_id"]
        left_message_id = payload["left_message_id"]
        link_type = payload["link_type"]

        await agg.unlink_message(
            right_message_id=message_id, 
            left_message_id=left_message_id, 
            mailbox_id=mailbox_id, 
            link_type=link_type
        )