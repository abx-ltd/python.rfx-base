from . import datadef
from . import Command
from .. import types

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
        direction = payload.direction
        if direction == types.DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender(
                message_id=agg.get_aggroot().identifier,
            )
            await agg.set_message_category(
                resource="message_sender",
                resource_id=message_sender._id,
                category=payload.category,
            )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id
            )
            await agg.set_message_category(
                resource="message_recipient",
                resource_id=message_recipient._id,
                category=payload.category,
            )

class RemoveMessageCategory(Command):
    """Remove the category of a message."""

    Data = datadef.RemoveMessageCategoryPayload

    class Meta:
        key = "remove-message-category"
        resources = ("message",)
        tags = ["message", "category"]
        auth_required = True

    Data = datadef.RemoveMessageCategoryPayload

    async def _process(self, agg, stm, payload):
        direction = payload.direction
        if direction == types.DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender(
                message_id=agg.get_aggroot().identifier,
            )
            await agg.remove_message_category(
                resource="message_sender",
                resource_id=message_sender._id,
            )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id
            )
            await agg.remove_message_category(
                resource="message_recipient",
                resource_id=message_recipient._id,
            )