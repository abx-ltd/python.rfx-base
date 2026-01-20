from . import datadef
from . import Command
from .. import types


class RemoveMessage(Command):
    """Remove a message from the current user."""

    Data = datadef.RemoveMessagePayload

    class Meta:
        key = "remove-message"
        resources = ("message",)
        tags = ["messages", "remove"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        direction = payload.direction

        if direction == types.DirectionTypeEnum.OUTBOUND:
            await agg.remove_message_sender(message_id=message_id)
        elif direction == types.DirectionTypeEnum.INBOUND:
            await agg.remove_message_recipient(message_id=message_id, profile_id=agg.get_context().profile_id)
