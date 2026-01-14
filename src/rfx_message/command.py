"""
Commands for the RFX messaging domain.
"""

from fluvius.data import serialize_mapping

from .domain import RFXMessageServiceDomain
from .helper import extract_template_context, determine_processing_mode
from .types import MessageTypeEnum, ProcessingModeEnum
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

    async def _process_message(self, agg, message_id, payload, mode):
        processed_message = await agg.process_message_content(
            message_id=message_id, context=extract_template_context(payload), mode=mode
        )

        await agg.mark_ready_for_delivery(message_id)
        return processed_message

    def _notify_recipient(
        self,
        client,
        recipients: list,
        kind: str,
        target: str,
        msg: dict,
        mode: ProcessingModeEnum,
    ):
        if not client:
            return ValueError("Client is not available")
        channels = []
        for profile_id in recipients:
            msg["recipient_id"] = profile_id
            channel = client.notify(
                profile_id=profile_id,
                kind=kind,
                target=target,
                msg=msg,
                batch_id=mode.value,
            )
            channels.append(channel)
        client.send(mode.value)
        return channels

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
        if message_category:
            await agg.set_message_category(
                resource="message", resource_id=message_id, category=message_category
            )

        # 3. Determine processing mode
        message_type = MessageTypeEnum(
            message_payload.get("message_type", "NOTIFICATION")
        )
        processing_mode = await determine_processing_mode(
            message_type=message_type, payload=message_payload
        )

        context = agg.get_context()
        client = context.service_proxy.mqtt_client
        message = await self._process_message(
            agg, message_id, message_payload, processing_mode
        )
        self._notify_recipient(
            client, recipients, "message", message_id, message, processing_mode
        )

        # Serialize message result and add category
        response_data = serialize_mapping(message_result)
        if message_category:
            response_data["category"] = message_category

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

    async def _process_message(self, agg, message_id, payload, mode):
        processed_message = await agg.process_message_content(
            message_id=message_id, context=extract_template_context(payload), mode=mode
        )

        await agg.mark_ready_for_delivery(message_id)
        return processed_message

    def _notify_recipient(
        self,
        client,
        recipients: list,
        kind: str,
        target: str,
        msg: dict,
        mode: ProcessingModeEnum,
    ):
        if not client:
            return ValueError("Client is not available")
        channels = []
        for profile_id in recipients:
            msg["recipient_id"] = profile_id
            channel = client.notify(
                profile_id=profile_id,
                kind=kind,
                target=target,
                msg=msg,
                batch_id=mode.value,
            )
            channels.append(channel)
        client.send(mode.value)
        return channels

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)

        message_category = message_payload.pop("category", None)

        # 1. Create reply message with same thread_id as parent
        message_result = await agg.reply_message(data=message_payload)
        message_id = message_result._id

        # 2.2. Set message category
        if message_category:
            await agg.set_message_category(
                resource="message", resource_id=message_id, category=message_category
            )

        # 3. Determine processing mode
        message_type = MessageTypeEnum(
            message_payload.get("message_type", "NOTIFICATION")
        )
        processing_mode = await determine_processing_mode(
            message_type=message_type, payload=message_payload
        )

        context = agg.get_context()
        client = context.service_proxy.mqtt_client
        message = await self._process_message(
            agg, message_id, message_payload, processing_mode
        )

        rootmsg = agg.get_rootobj()
        recipients = [rootmsg.sender_id]
        await agg.add_recipients(data=recipients, message_id=message_id)

        self._notify_recipient(
            client, recipients, "message", message_id, message, processing_mode
        )

        # Serialize message result and add category
        response_data = serialize_mapping(message_result)
        if message_category:
            response_data["category"] = message_category

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
        if payload.recipient_id:
            await agg.set_message_category(
                resource="message_recipient",
                resource_id=payload.recipient_id,
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
        resources = ("message_recipient",)
        tags = ["message", "read"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.mark_message_read()


class MarkAllMessagesRead(Command):
    """Mark all messages as read for the current user."""

    class Meta:
        key = "mark-all-message-read"
        new_resource = True
        resources = ("message_recipient",)
        tags = ["messages", "read"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.mark_all_messages_read()


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
