# Command definitions
# Define command classes here
from datetime import datetime, timedelta
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.data.exceptions import ItemNotFoundError
from fluvius.domain.activity import ActivityType
from fluvius.error import BadRequestError
from .domain import RFX2DMessageDomain
from .types import DirectionTypeEnum

from . import datadef, config, logger, helper

Command = RFX2DMessageDomain.Command


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

        # yield agg.create_response(
        #     {
        #         "Message": "Mailbox created successfully"
        #     },
        #     serialize_mapping(mailbox_result),
        #     _type="message-response"
        # )


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


# class AddMemberToMailbox(Command):
#     Data = datadef.AddMemberToMailboxPayload

#     class Meta:
#         key = "add-member-to-mailbox"
#         resources = ("mailbox",)
#         tags = ["mailbox", "member", "add"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         mailbox_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id
#         payload = serialize_mapping(payload)

#         result = await agg.add_member_to_mailbox(mailbox_id=mailbox_id, 
#                                                  profile_id=profile_id, 
#                                                  member_ids=payload.get("profile_ids", [])
#                                                  )

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )

# class RemoveMemberFromMailbox(Command):
#     class Meta:
#         key = "remove-member-from-mailbox"
#         resources = ("mailbox",)
#         tags = ["mailbox", "member", "remove"]
#         auth_required = True
    
#     async def _process(self, agg, stm, payload):
#         mailbox_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id
#         payload = serialize_mapping(payload)

#         result = await agg.remove_member_from_mailbox(mailbox_id=mailbox_id, 
#                                                  profile_id=profile_id, 
#                                                  member_ids=payload.get("profile_ids", [])
#                                                  )

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )


# class CreateMailboxMessage(Command):
#     Data = datadef.CreateMailboxMessagePayload

#     class Meta:
#         key = "create-mailbox-message"
#         resources = ("mailbox",)
#         tags = ["mailbox", "message", "create"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         mailbox_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         result = await agg.create_mailbox_message(data=payload, mailbox_id=mailbox_id, profile_id=profile_id)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )


# class RemoveMailboxMessage(Command):
#     class Meta:
#         key = "remove-mailbox-message"
#         resources = ("mailbox",)
#         tags = ["mailbox", "message", "remove"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         mailbox_message_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         result = await agg.remove_mailbox_message(mailbox_message_id=mailbox_message_id, profile_id=profile_id)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )

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
        await agg.assign_message_recipient(message_id=message_id, mailbox_id=mailbox_id, recipients=recipients)

        # 6. Determine processing mode and get client
        processing_mode, client = await helper.get_processing_mode_and_client(
            agg, message_payload
        )

        # # 7. Process message content
        # message = await helper.determine_and_process_message(
        #     agg, message_id, message_payload, processing_mode
        # )

        # user_ids = await stm.get_user_ids_from_profile_ids(recipients)

        # # 8. Notify recipients
        # helper.notify_recipients(
        #     client,
        #     recipients,
        #     user_ids,
        #     "message",
        #     message_id,
        #     message,
        #     processing_mode,
        # )

        # 9. Create response
        response_data = serialize_mapping(message_result)

        yield agg.create_response(
            response_data,
            _type="message-response",
        )

# class UpdateMessageSender(Command):
#     """Update a message for the current user, is archived or is starred"""
#     Data = datadef.UpdateMessagePayload

#     class Meta:
#         key = "update-message"
#         resources = ("message",)
#         tags = ["messages", "update"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         message_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         direction = payload.direction
#         if direction == DirectionTypeEnum.OUTBOUND:
#             await agg.update_message_sender(
#                 message_id=message_id, 
#                 profile_id=profile_id, 
#                 data=payload
#             )

#         elif direction == DirectionTypeEnum.INBOUND:
#             await agg.update_message_recipient(
#                 message_id=message_id, 
#                 profile_id=profile_id, 
#                 data=payload
#             )

# class RemoveMessage(Command):
#     """Remove message for the current user"""
#     class Meta:
#         key = "remove-message"
#         resources = ("message",)
#         tags = ["messages", "remove"]
#         auth_required = True
#         policy_required = False

#     Data = datadef.RemoveMessagePayload

#     async def _process(self, agg, stm, payload):
#         message_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         direction = payload.direction

#         if direction == DirectionTypeEnum.OUTBOUND:
#             await agg.remove_message_sender(
#                 message_id=message_id, profile_id=profile_id
#             )
#         elif direction == DirectionTypeEnum.INBOUND:
#             await agg.remove_message_recipient(
#                 message_id=message_id, profile_id=profile_id
#             )

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
        await agg.update_tag(data=payload)


class RemoveTag(Command):
    """Remove a tag."""

    class Meta:
        key = "remove-tag"
        resources = ("tag",)
        tags = ["tag", "remove"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        tag = await agg.find_tag(tag_id=agg.get_aggroot().identifier)
        await agg.remove_message_tag_from_tag(tag_id=tag._id)
        await agg.remove_tag()

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
        direction = payload.direction

        if direction == DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender_by_message_id(
                message_id=agg.get_aggroot().identifier
            )
            for tag_id in payload.tag_ids:
                await agg.add_message_tag(
                    resource="message_sender",
                    resource_id=message_sender._id,
                    tag_id=tag_id,
                )
        elif direction == DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            for tag_id in payload.tag_ids:
                await agg.add_message_tag(
                    resource="message_recipient",
                    resource_id=message_recipient._id,
                    tag_id=tag_id,
                )

class RemoveMessageTag(Command):
    """Remove a message from a tag."""

    Data = datadef.RemoveMessageTagPayload

    class Meta:
        key = "remove-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        direction = payload.direction
        if direction == DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender_by_message_id(
                message_id=agg.get_aggroot().identifier,
            )
            for tag_id in payload.tag_ids:
                await agg.remove_message_tag_from_resource(
                    resource="message_sender",
                    resource_id=message_sender._id,
                    tag_id=tag_id,
                )
        elif direction == DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            for tag_id in payload.tag_ids:
                await agg.remove_message_tag_from_resource(
                    resource="message_recipient",
                    resource_id=message_recipient._id,
                    tag_id=tag_id,
                )

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
        profile_id = agg.get_context().profile_id

        payload = serialize_mapping(payload)

        result = await agg.add_message_to_category(data=payload, category_id=category_id, profile_id=profile_id)

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

        # payload = serialize_mapping(payload)

        result = await agg.remove_message_from_category(data=payload, category_id=category_id, profile_id=profile_id)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


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

        result = await agg.assign_message(
            message_id=message_id,
            mailbox_id=payload.mailbox_id,
            assignee_profile_id=payload.assignee_profile_id,
        )

        # # Determine processing mode and get client
        # processing_mode, client = await helper.get_processing_mode_and_client(
        #     agg, message_payload
        # )

        # # Process message content
        # message = await helper.determine_and_process_message(
        #     agg, message_id, message_payload, processing_mode
        # )

        # user_ids = await stm.get_user_ids_from_profile_ids(recipients)

        # # Notify recipients
        # helper.notify_recipients(
        #     client,
        #     recipients,
        #     user_ids,
        #     "message",
        #     message_id,
        #     message,
        #     processing_mode,
        # )

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

        # yield agg.create_activity(
        #     logroot=agg.get_aggroot(),
        #     message=f"Set status for message {message_id} to {payload.message_status}",
        #     msglabel="set-message-status",
        #     msgtype=ActivityType.USER_ACTION,
        #     data={"message_status": payload.message_status},
        # )

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

        result = await agg.move_message(
            message_id=message_id,
            mailbox_id=payload.mailbox_id,
            folder=payload.folder,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Moved message {message_id} to folder {payload.folder} in mailbox {payload.mailbox_id}",
            msglabel="move-message",
            msgtype=ActivityType.USER_ACTION,
            data={"mailbox_id": str(payload.mailbox_id), "folder": payload.folder},
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

        result = await agg.set_message_star(
            message_id=message_id,
            mailbox_id=payload.mailbox_id,
            starred=payload.starred,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Set star={payload.starred} for message {message_id} in mailbox {payload.mailbox_id}",
            msglabel="set-message-star",
            msgtype=ActivityType.USER_ACTION,
            data={"mailbox_id": str(payload.mailbox_id), "starred": payload.starred},
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

        result = await agg.set_priority(
            message_id=message_id,
            priority=payload.priority,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Set priority for message {message_id} to {payload.priority}",
            msglabel="set-priority",
            msgtype=ActivityType.USER_ACTION,
            data={"priority": payload.priority},
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class LinkRelatedMessage(Command):
    """Link two related messages."""

    Data = datadef.LinkRelatedMessagePayload

    class Meta:
        key = "link-related-message"
        resources = ("message",)
        tags = ["message", "link"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        result = await agg.link_related_message(
            message_id=message_id,
            related_message_id=payload.related_message_id,
            link_type=payload.link_type,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Linked message {message_id} with related message {payload.related_message_id}",
            msglabel="link-related-message",
            msgtype=ActivityType.USER_ACTION,
            data={"related_message_id": str(payload.related_message_id), "link_type": payload.link_type},
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


class UploadAttachmentMetadata(Command):
    """Register metadata for an uploaded attachment."""

    Data = datadef.UploadAttachmentMetadataPayload

    class Meta:
        key = "upload-attachment-metadata"
        resources = ("message",)
        tags = ["message", "attachment"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier

        result = await agg.upload_attachment_metadata(
            message_id=message_id,
            data=payload,
        )

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"Registered attachment metadata for message {message_id}",
            msglabel="upload-attachment-metadata",
            msgtype=ActivityType.USER_ACTION,
            data={
                "filename": payload.filename,
                "storage_key": payload.storage_key,
                "media_type": payload.media_type,
                "size_bytes": payload.size_bytes,
            },
        )

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
        )


# class CreateTag(Command):
#     """Create a new tag for the current user"""
#     Data = datadef.CreateTagPayload

#     class Meta:
#         key = "create-tag"
#         resource_init = True
#         resources = ("tag",)
#         tags = ["tag", "create"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         result = await agg.create_tag(data=payload)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )


# class UpdateTag(Command):
#     """Update a tag."""

#     Data = datadef.UpdateTagPayload

#     class Meta:
#         key = "update-tag"
#         resources = ("tag",)
#         tags = ["tag", "update"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         await agg.update_tag(data=payload)


# class RemoveTag(Command):
#     """Remove a tag."""

#     class Meta:
#         key = "remove-tag"
#         resources = ("tag",)
#         tags = ["tag", "remove"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         tag = await agg.find_tag(tag_id=agg.get_aggroot().identifier)
#         await agg.remove_message_tag_from_tag(tag_id=tag._id)
#         await agg.remove_tag()


# class AddMessageTag(Command):
#     """Add a message to a tag"""

#     Data = datadef.AddMessageTagPayload

#     class Meta:
#         key = "add-message-tag"
#         resources = ("message",)
#         tags = ["message", "tag"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         direction = payload.direction

#         if direction == DirectionTypeEnum.OUTBOUND:
#             message_sender = await agg.get_message_sender_by_message_id(
#                 message_id=agg.get_aggroot().identifier
#             )
#             for tag_id in payload.tag_ids:
#                 await agg.add_message_tag(
#                     resource="message_sender",
#                     resource_id=message_sender._id,
#                     tag_id=tag_id,
#                 )
#         elif direction == DirectionTypeEnum.INBOUND:
#             message_recipient = await agg.get_message_recipient(
#                 message_id=agg.get_aggroot().identifier,
#                 profile_id=agg.get_context().profile_id,
#             )
#             for tag_id in payload.tag_ids:
#                 await agg.add_message_tag(
#                     resource="message_recipient",
#                     resource_id=message_recipient._id,
#                     tag_id=tag_id,
#                 )


# class RemoveMessageTag(Command):
#     """Remove a message from a tag."""

#     Data = datadef.RemoveMessageTagPayload

#     class Meta:
#         key = "remove-message-tag"
#         resources = ("message",)
#         tags = ["message", "tag"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         direction = payload.direction
#         if direction == DirectionTypeEnum.OUTBOUND:
#             message_sender = await agg.get_message_sender_by_message_id(
#                 message_id=agg.get_aggroot().identifier,
#             )
#             for tag_id in payload.tag_ids:
#                 await agg.remove_message_tag_from_resource(
#                     resource="message_sender",
#                     resource_id=message_sender._id,
#                     tag_id=tag_id,
#                 )
#         elif direction == DirectionTypeEnum.INBOUND:
#             message_recipient = await agg.get_message_recipient(
#                 message_id=agg.get_aggroot().identifier,
#                 profile_id=agg.get_context().profile_id,
#             )
#             for tag_id in payload.tag_ids:
#                 await agg.remove_message_tag_from_resource(
#                     resource="message_recipient",
#                     resource_id=message_recipient._id,
#                     tag_id=tag_id,
#                 )


# class CreateCategory(Command):
#     Data = datadef.CreateCategoryPayload

#     class Meta:
#         key = "create-category"
#         resources = ("category",)
#         resource_init = True
#         tags = ["category", "create"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         profile_id = agg.get_context().profile_id

#         result = await agg.create_category(data=payload, profile_id=profile_id)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )


# class RemoveCategory(Command):

#     class Meta:
#         key = "remove-category"
#         resources = ("category",)
#         tags = ["category", "remove"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         category_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         await agg.remove_category(category_id=category_id, profile_id=profile_id)


# class AddMessageCategory(Command):
#     Data = datadef.AddMessageCategoryPayload

#     class Meta:
#         key = "add-message-category"
#         resources = ("category",)
#         tags = ["message", "category"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         category_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         payload = serialize_mapping(payload)

#         result = await agg.add_message_to_category(data=payload, category_id=category_id, profile_id=profile_id)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )


# class RemoveMessageCategory(Command):

#     Data = datadef.RemoveMessageCategoryPayload

#     class Meta:
#         key = "remove-message-category"
#         resources = ("category",)
#         tags = ["message", "category"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         category_id = agg.get_aggroot().identifier
#         profile_id = agg.get_context().profile_id

#         # payload = serialize_mapping(payload)

#         result = await agg.remove_message_from_category(data=payload, category_id=category_id, profile_id=profile_id)

#         yield agg.create_response(
#             serialize_mapping(result),
#             _type="message-response",
#         )
