from fluvius.data import serialize_mapping
from . import datadef
from . import Command
from . import helper


class SendMessage(Command):
    """
    Send a notification message to recipients.

    Supports both template-based and direct content messages.
    """

    Data = datadef.SendMessagePayload

    class Meta:
        key = "send-message"
        resource_init = True
        resources = ("message",)
        tags = ["message"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_payload = serialize_mapping(payload)
        recipients = message_payload.pop("recipients", None)
        if not recipients:
            raise ValueError("Recipients list cannot be empty")

        profile_id = agg.get_context().profile_id

        # 1. Create message record
        message_result = await agg.generate_message(
            data=message_payload, sender_id=profile_id
        )
        message_id = message_result._id

        # 2. Add sender to message_sender
        await agg.add_sender(message_id=message_id, sender_id=profile_id)

        # 3. Add recipients and set message category
        await agg.add_recipients(data=recipients, message_id=message_id)

        # 3. Determine processing mode and get client
        processing_mode, client = await helper.get_processing_mode_and_client(
            agg, message_payload
        )

        # 5. Process message content
        message = await helper.determine_and_process_message(
            agg, message_id, message_payload, processing_mode
        )

        # 6. Notify recipients
        helper.notify_recipients(
            client, recipients, "message", message_id, message, processing_mode
        )

        # 7. Create response
        response_data = serialize_mapping(message_result)

        yield agg.create_response(
            response_data,
            _type="message-service-response",
        )
