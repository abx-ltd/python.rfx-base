from . import datadef
from . import Command


class UpdateMessageCategory(Command):
    """Set the category of a message."""

    Data = datadef.UpdateMessageCategoryPayload

    class Meta:
        key = "update-message-category"
        resources = ("message",)
        tags = ["message", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        category = payload.category
        await agg.update_message_category(category=category)


class RemoveMessageCategory(Command):
    """Remove the category of a message."""

    class Meta:
        key = "remove-message-category"
        resources = ("message",)
        tags = ["message", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_message_category()
