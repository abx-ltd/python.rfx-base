from fluvius.data import serialize_mapping

from . import datadef
from . import Command
from . import helper


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

        # 1. Create reply message with same thread_id as parent
        message_result = await agg.reply_message(data=message_payload)
        message_id = message_result._id

        # 2. Add sender to message_sender
        await agg.add_sender(
            message_id=message_id, sender_id=agg.get_context().profile_id
        )

        # 4. Determine processing mode and get client
        processing_mode, client = await helper.get_processing_mode_and_client(
            agg, message_payload
        )

        # 5. Process message content
        message = await helper.determine_and_process_message(
            agg, message_id, message_payload, processing_mode
        )

        # 6. Get recipients from root message and add them
        message_sender = await agg.get_message_sender_by_message_id(
            message_id=agg.get_aggroot().identifier,
        )
        recipients = [message_sender.sender_id]
        await agg.add_recipients(data=recipients, message_id=message_id)

        # 7. Notify recipients
        helper.notify_recipients(
            client, recipients, "message", message_id, message, processing_mode
        )

        # 8. Create response
        response_data = serialize_mapping(message_result)

        yield agg.create_response(
            response_data,
            _type="message-service-response",
        )
