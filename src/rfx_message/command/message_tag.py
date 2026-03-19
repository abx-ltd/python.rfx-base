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
            message_sender = await agg.get_message_sender_by_message_id(
                message_id=agg.get_aggroot().identifier
            )
            for tag_id in payload.tag_ids:
                await agg.add_message_tag(
                    resource="message_sender",
                    resource_id=message_sender._id,
                    tag_id=tag_id,
                )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            for tag_id in payload.tag_ids:
                await agg.add_message_tag(
                    resource="message_recipient",
                    resource_id=message_recipient._id,
                    tag_id=tag_id,
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
            message_sender = await agg.get_message_sender_by_message_id(
                message_id=agg.get_aggroot().identifier,
            )
            for tag_id in payload.tag_ids:
                await agg.remove_message_tag_from_resource(
                    resource="message_sender",
                    resource_id=message_sender._id,
                    tag_id=tag_id,
                )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            for tag_id in payload.tag_ids:
                await agg.remove_message_tag_from_resource(
                    resource="message_recipient",
                    resource_id=message_recipient._id,
                    tag_id=tag_id,
                )


class UpdateAllMessageTags(Command):
    """Update all tags for a message."""

    Data = datadef.UpdateAllMessageTagsPayload

    class Meta:
        key = "update-all-message-tag"
        resources = ("message",)
        tags = ["message", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        direction = payload.direction
        if direction == types.DirectionTypeEnum.OUTBOUND:
            message_sender = await agg.get_message_sender_by_message_id(
                message_id=agg.get_aggroot().identifier
            )
            await agg.remove_all_message_tags_from_resource(
                resource="message_sender",
                resource_id=message_sender._id,
            )
            await agg.add_message_tags_to_resource(
                resource="message_sender",
                resource_id=message_sender._id,
                tag_ids=payload.tag_ids,
            )
        elif direction == types.DirectionTypeEnum.INBOUND:
            message_recipient = await agg.get_message_recipient(
                message_id=agg.get_aggroot().identifier,
                profile_id=agg.get_context().profile_id,
            )
            await agg.remove_all_message_tags_from_resource(
                resource="message_recipient",
                resource_id=message_recipient._id,
            )
            await agg.add_message_tags_to_resource(
                resource="message_recipient",
                resource_id=message_recipient._id,
                tag_ids=payload.tag_ids,
            )
