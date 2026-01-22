from . import datadef
from . import Command
from .. import types


class AddMessageTag(Command):
    """Add a tag to a message."""

    Data = datadef.AddMessageTagPayload

    class Meta:
        key = "add-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    Data = datadef.AddMessageTagPayload

    async def _process(self, agg, stm, payload):
        direction = payload.direction
        if direction == types.DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender(
                message_id=agg.get_aggroot().identifier
            )
            await agg.add_message_tag(
                resource="message_sender",
                resource_id=message_sender._id,
                key=payload.key,
            )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            await agg.add_message_tag(
                resource="message_recipient",
                resource_id=message_recipient._id,
                key=payload.key,
            )


class RemoveMessageTag(Command):
    """Remove a tag from a message."""

    Data = datadef.RemoveMessageTagPayload

    class Meta:
        key = "remove-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        direction = payload.direction
        if direction == types.DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender(
                message_id=agg.get_aggroot().identifier,
            )
            await agg.remove_message_tag(
                resource="message_sender",
                resource_id=message_sender._id,
                key=payload.key,
            )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            await agg.remove_message_tag(
                resource="message_recipient",
                resource_id=message_recipient._id,
                key=payload.key,
            )
