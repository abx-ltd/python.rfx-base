from . import datadef
from . import Command
from .. import types


class RestoreMessage(Command):
    """Restore a message from trashed/archived to inbox/outbox for the current user."""

    Data = datadef.RestoreMessagePayload

    class Meta:
        key = "restore-message"
        resources = ("message",)
        tags = ["messages", "restore"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        direction = payload.direction

        send_to_themselves = False
        if direction == types.DirectionTypeEnum.OUTBOUND:
            send_to_themselves = await agg.check_message_recipient(
                message_id, agg.get_context().profile_id
            )

        inbox_box = await agg.get_message_box("inbox")
        outbox_box = await agg.get_message_box("outbox")

        if send_to_themselves:
            await agg.change_sender_box_id(
                message_id=message_id,
                box_id=outbox_box._id,
                profile_id=agg.get_context().profile_id,
            )
            await agg.change_recipient_box_id(
                message_id=message_id,
                box_id=inbox_box._id,
                profile_id=agg.get_context().profile_id,
            )
            await agg.change_all_sender_box_id_of_same_thread(
                outbox_box._id, agg.get_context().profile_id
            )
            await agg.change_all_recipient_box_id_of_same_thread(
                inbox_box._id, agg.get_context().profile_id
            )
        else:
            if direction == types.DirectionTypeEnum.OUTBOUND:
                await agg.change_sender_box_id(
                    message_id=message_id,
                    box_id=outbox_box._id,
                    profile_id=agg.get_context().profile_id,
                )
                await agg.change_all_sender_box_id_of_same_thread(
                    outbox_box._id, agg.get_context().profile_id
                )
                await agg.change_all_recipient_box_id_of_same_thread(
                    inbox_box._id, agg.get_context().profile_id
                )
            elif direction == types.DirectionTypeEnum.INBOUND:
                await agg.change_recipient_box_id(
                    message_id=message_id,
                    box_id=inbox_box._id,
                    profile_id=agg.get_context().profile_id,
                )
