from . import datadef
from . import Command
from . import types


class ArchiveMessage(Command):
    """Archive a message for the current user."""

    Data = datadef.ArchiveMessagePayload

    class Meta:
        key = "archive-message"
        resources = ("message",)
        tags = ["messages", "archived"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        message_id = agg.get_aggroot().identifier
        direction = payload.direction

        archived_box = await agg.get_message_box("archived")

        if direction == types.DirectionTypeEnum.OUTBOUND:
            await agg.change_sender_box_id(
                message_id=message_id,
                box_id=archived_box._id,
                profile_id=agg.get_context().profile_id,
            )

            # archive all message sender in the thread
            await agg.change_all_sender_box_id_of_same_thread(
                archived_box._id, agg.get_context().profile_id
            )
            # for message in serialize_mapping(messages):
            #     await agg.change_sender_box_id_if_exist(
            #         message_id=message._id,
            #         box_id=archived_box._id,
            #         profile_id=agg.get_context().profile_id,
            #     )
        elif direction == types.DirectionTypeEnum.INBOUND:
            await agg.change_recipient_box_id(
                message_id=message_id,
                box_id=archived_box._id,
                profile_id=agg.get_context().profile_id,
            )
