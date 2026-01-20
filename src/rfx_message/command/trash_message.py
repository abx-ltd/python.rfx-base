from . import datadef
from . import Command
from .. import types

class TrashMessage(Command):
    """Trash a message for the current user."""

    Data = datadef.TrashMessagePayload

    class Meta:
        key = "trash-message"
        resources = ("message",)
        tags = ["messages", "trashed"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        direction = payload.direction

        trashed_box = await agg.get_message_box("trashed")

        send_to_themselves = False
        if direction == types.DirectionTypeEnum.OUTBOUND:
            send_to_themselves = await agg.check_message_recipient(message_id)
        elif direction == types.DirectionTypeEnum.INBOUND:
            send_to_themselves = await agg.check_message_sender(message_id)

        if send_to_themselves:
            await agg.change_sender_box_id(
                message_id=message_id, box_id=trashed_box._id
            )
            await agg.change_recipient_box_id(
                message_id=message_id, box_id=trashed_box._id
            )
        else:
            if direction == types.DirectionTypeEnum.OUTBOUND:
                await agg.change_sender_box_id(
                    message_id=message_id, box_id=trashed_box._id
                )
            elif direction == types.DirectionTypeEnum.INBOUND:
                await agg.change_recipient_box_id(
                    message_id=message_id, box_id=trashed_box._id
                )

