from fluvius.domain.aggregate import action

from ..types import (
    MessageCategoryEnum,
)


class MessageCategoryMixin:
    @action(
        "message-category-set",
        resources=("message",),
    )
    async def set_message_category(self, ):



    @action(
        "message-category-remove",
        resources=("message", "message_recipient", "message_category"),
    )
    async def remove_message_category(self, *, resource: str, resource_id: str):
        """Action to remove the category of a message."""
        message_category = await self.statemgr.find_one(
            "message_category",
            where={
                "resource": resource,
                "resource_id": resource_id,
            },
        )
        await self.statemgr.invalidate(message_category)
