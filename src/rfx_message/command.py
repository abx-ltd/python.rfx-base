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

    def _notify_recipients(
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
        for user_id in recipients:
            msg["recipient_id"] = user_id
            channel = client.notify(
                user_id=user_id, kind=kind, target=target, msg=msg, batch_id=mode.value
            )
            channels.append(channel)
        client.send(mode.value)
        return channels

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)
        recipients = message_payload.pop("recipients", None)

        if not recipients:
            raise ValueError("Recipients list cannot be empty")

        # 1. Create message record
        message_result = await agg.generate_message(data=message_payload)
        message_id = message_result["message_id"]

        # 2. Add recipients
        await agg.add_recipients(data=recipients, message_id=message_id)

        # 3. Determine processing mode
        message_type = MessageTypeEnum(
            message_payload.get("message_type", "NOTIFICATION")
        )
        processing_mode = await determine_processing_mode(
            message_type=message_type, payload=message_payload
        )

        context = agg.get_context()
        client = context.service_proxy.mqtt_client
        channels = []
        message = await self._process_message(
            agg, message_id, message_payload, processing_mode
        )
        channels = self._notify_recipients(
            client, recipients, "message", message_id, message, processing_mode
        )

        yield agg.create_response(
            {
                "status": "success",
                "message_id": message_id,
                "processing_mode": processing_mode.value,
                "recipients_count": len(recipients),
                "channels": channels,
            },
            _type="message-service-response",
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
        # Substitute for the next Fluvius Batch update
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
        resources = ("message_recipient",)
        tags = ["messages", "archived"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.archive_message()


class ReplyMessage(Command):
    """Reply to a message."""

    class Meta:
        key = "reply-message"
        resources = ("message_recipient",)
        tags = ["message", "reply"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.reply_message()

        yield agg.create_response(
            serialize_mapping(result), _type="message-service-response"
        )


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
