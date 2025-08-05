from fluvius.data import serialize_mapping, UUID_GENR

from .domain import MessageServiceDomain
from . import datadef

processor = MessageServiceDomain.command_processor
Command = MessageServiceDomain.Command

class SendMessage(Command):
    """
    Send a message to recipients.
    """

    Data = datadef.SendMessagePayload

    class Meta:
        key = "send-message"
        new_resource = True
        resources = ("message",)
        tags = ["message", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        context = agg.get_context()

        message_data = serialize_mapping(payload)
        message_data['sender_id'] = context.user_id

        recipients = message_data.pop("recipients", [])
        message = await agg.create_message(data=message_data)
        if recipients:
            recipients = await agg.add_recipients(data=recipients, message_id=message["message_id"])

        yield agg.create_response(serialize_mapping(message), _type="message-service-response")


# TODO: Implement other actions like update, delete, etc.
class ReadMessage(Command):
    """
    Mark a message or all unread messages as read
    """

    class Meta:
        key = "read-message"
        resources = ("message-recipient",)
        tags = ["message", "read"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        pass