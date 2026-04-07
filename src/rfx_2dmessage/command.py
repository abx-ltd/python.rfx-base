# Command definitions
# Define command classes here
from datetime import datetime, timedelta
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.data.exceptions import ItemNotFoundError
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

        result = await agg.create_mailbox(data=payload, profile_id=profile_id)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-response",
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

# class SendMessage(Command):
#     """
#     Send a notification message to recipients.

#     Supports both template-based and direct content messages.
#     """

#     Data = datadef.SendMessagePayload

#     class Meta:
#         key = "send-message"
#         resource_init = True
#         resources = ("message",)
#         tags = ["message"]
#         auth_required = True
#         policy_required = False

#     async def _process(self, agg, stm, payload):
#         message_payload = serialize_mapping(payload)
#         recipients = message_payload.pop("recipients", None)
#         if not recipients:
#             raise ValueError("Recipients list cannot be empty")

#         profile_id = agg.get_context().profile_id

#         # 1. Create message record
#         message_result = await agg.generate_message(
#             data=message_payload, sender_id=profile_id
#         )
#         message_id = message_result._id

#         # 2. Add sender to message_sender
#         sender_result = await agg.add_sender(message_id=message_id, 
#                                           sender_id=profile_id, 
#                                           recipients=recipients
#         )

#         box_id = sender_result["box_id"]

#         # 3. Add recipients and set message category
#         await agg.add_recipients(
#             data=recipients, 
#             message_id=message_id,
#             box_id=box_id
#         )

#         # 3. Determine processing mode and get client
#         processing_mode, client = await helper.get_processing_mode_and_client(
#             agg, message_payload
#         )

#         # 5. Process message content
#         message = await helper.determine_and_process_message(
#             agg, message_id, message_payload, processing_mode
#         )

#         user_ids = await stm.get_user_ids_from_profile_ids(recipients)

#         print("VALUE QUERY RESULT:", user_ids)
        
#         # 6. Notify recipients
#         helper.notify_recipients(
#             client,
#             recipients,
#             user_ids,
#             "message",
#             message_id,
#             message,
#             processing_mode,
#         )

#         # 7. Create response
#         response_data = serialize_mapping(message_result)

#         yield agg.create_response(
#             response_data,
#             _type="message-response",
#         )

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


