"""
Commands for the RFX messaging domain.
"""

from fluvius.data import serialize_mapping

from .domain import RFXMessageServiceDomain
from .helper import (
    notify_recipients,
    set_message_category_if_provided,
    determine_and_process_message,
    get_processing_mode_and_client,
    create_message_response,
)
from . import datadef

processor = RFXMessageServiceDomain.command_processor
Command = RFXMessageServiceDomain.Command


class SendMessage(Command):
    """
    Send a notification message to recipients.

    Supports both template-based and direct content messages.
    """

    Data = datadef.SendMessagePayload

    class Meta:
        key = "send-message"
        new_resource = True
        resources = ("message",)
        tags = ["message"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)
        recipients = message_payload.pop("recipients", None)
        message_category = message_payload.pop("category", None)
        if not recipients:
            raise ValueError("Recipients list cannot be empty")

        profile_id = agg.get_context().profile_id

        # 1. Create message record
        message_result = await agg.generate_message(
            data=message_payload, sender_id=profile_id
        )
        message_id = message_result._id

        # 2. Add recipients and set message category
        await agg.add_recipients(data=recipients, message_id=message_id)

        # 2.2. Set message category
        await set_message_category_if_provided(agg, message_id, message_category)

        # 3. Determine processing mode and get client
        processing_mode, client = await get_processing_mode_and_client(
            agg, message_payload
        )

        # 4. Process message content
        message = await determine_and_process_message(
            agg, message_id, message_payload, processing_mode
        )

        # 5. Notify recipients
        notify_recipients(
            client, recipients, "message", message_id, message, processing_mode
        )

        # 6. Create response
        response_data = create_message_response(message_result, message_category)

        yield agg.create_response(
            response_data,
            _type="message-service-response",
        )


class ReplyMessage(Command):
    """Reply to a message."""

    Data = datadef.ReplyMessagePayload

    class Meta:
        key = "reply-message"
        resources = ("message",)
        tags = ["message", "reply"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)

        message_category = message_payload.pop("category", None)

        # 1. Create reply message with same thread_id as parent
        message_result = await agg.reply_message(data=message_payload)
        message_id = message_result._id

        # 2. Set message category
        await set_message_category_if_provided(agg, message_id, message_category)

        # 3. Determine processing mode and get client
        processing_mode, client = await get_processing_mode_and_client(
            agg, message_payload
        )

        # 4. Process message content
        message = await determine_and_process_message(
            agg, message_id, message_payload, processing_mode
        )

        # 5. Get recipients from root message and add them
        rootmsg = agg.get_rootobj()
        recipients = [rootmsg.sender_id]
        await agg.add_recipients(data=recipients, message_id=message_id)

        # 6. Notify recipients
        notify_recipients(
            client, recipients, "message", message_id, message, processing_mode
        )

        # 7. Create response
        response_data = create_message_response(message_result, message_category)

        yield agg.create_response(
            response_data,
            _type="message-service-response",
        )


class SetMessageCategory(Command):
    """Set the category of a message."""

    Data = datadef.SetMessageCategoryPayload

    class Meta:
        key = "set-message-category"
        resources = ("message",)
        tags = ["message", "category"]
        auth_required = True

    Data = datadef.SetMessageCategoryPayload

    async def _process(self, agg, stm, payload):
        message_recipient = await agg.get_message_recipient(
            message_id=agg.get_aggroot().identifier
        )
        if payload.recipient_id:
            await agg.set_message_category(
                resource="message_recipient",
                resource_id=message_recipient._id,
                category=payload.category,
            )
        else:
            await agg.set_message_category(
                resource="message",
                resource_id=agg.get_aggroot().identifier,
                category=payload.category,
            )


class ReadMessage(Command):
    """Mark a message as read for the current user."""

    class Meta:
        key = "read-message"
        resources = ("message",)
        tags = ["message", "read"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.mark_message_read()


class MarkAllMessagesRead(Command):
    """Mark all messages as read for the current user."""

    class Meta:
        key = "mark-all-message-read"
        resources = ("message",)
        new_resource = True
        tags = ["messages", "read"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        read_count = await agg.mark_all_messages_read()
        yield agg.create_response(
            serialize_mapping(read_count),
            _type="message-service-response",
        )


class ArchiveMessage(Command):
    """Archive a message for the current user."""

    class Meta:
        key = "archive-message"
        resources = ("message",)
        tags = ["messages", "archived"]
        auth_required = True
        policy_required = False

    Data = datadef.ArchiveMessagePayload

    async def _process(self, agg, stm, payload):
        await agg.archive_message(payload)


class TrashMessage(Command):
    """Trash a message for the current user."""

    class Meta:
        key = "trash-message"
        resources = ("message",)
        tags = ["messages", "trashed"]
        auth_required = True
        policy_required = False

    Data = datadef.TrashMessagePayload

    async def _process(self, agg, stm, payload):
        await agg.trash_message(payload)


# Template management commands


class CreateTemplate(Command):
    """Create a new message template."""

    Data = datadef.CreateTemplatePayload

    class Meta:
        key = "create-template"
        new_resource = True
        resources = ("message_template",)
        tags = ["template", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.create_template(data=serialize_mapping(payload))

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )


class UpdateTemplate(Command):
    """Update a template"""

    Data = datadef.CreateTemplatePayload

    class Meta:
        key = "update-template"
        resource = "message_template"
        tags = ["template", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.update_template(data=serialize_mapping(payload))

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )


class PublishTemplate(Command):
    """Publish a template to make it available."""

    # Data = datadef.PublishTemplatePayload

    class Meta:
        key = "publish-template"
        resources = ("message_template",)
        tags = ["template", "publish"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.publish_template()

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )
