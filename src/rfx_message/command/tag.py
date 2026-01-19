from . import datadef
from . import Command
from fluvius.data import serialize_mapping

class CreateTag(Command):
    """Create a new tag."""

    Data = datadef.CreateTagPayload

    class Meta:
        key = "create-tag"
        new_resource = True
        resources = ("tag",)
        tags = ["tag", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.create_tag(data=payload)

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )


class UpdateTag(Command):
    """Update a tag."""

    Data = datadef.UpdateTagPayload

    class Meta:
        key = "update-tag"
        resources = ("tag",)
        tags = ["tag", "update"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.update_tag(data=payload)


class RemoveTag(Command):
    """Remove a tag."""

    class Meta:
        key = "remove-tag"
        resources = ("tag",)
        tags = ["tag", "remove"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        await agg.remove_tag(data=payload)
