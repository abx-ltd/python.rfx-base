from . import Command
from fluvius.data import serialize_mapping


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
