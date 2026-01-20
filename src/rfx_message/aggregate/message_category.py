from fluvius.domain.aggregate import action

from ..types import (
    MessageCategoryEnum,
)


class MessageCategoryMixin:
    @action(
        "message-category-set",
        resources=("message", "message_recipient", "message_category"),
    )
    async def set_message_category(
        self, *, resource: str, resource_id: str, category: MessageCategoryEnum
    ):
        """Action to set the category of a message."""
        message_category = await self.statemgr.exists(
            "message_category",
            {
                "resource": resource,
                "resource_id": resource_id,
            },
        )
        if message_category:
            await self.statemgr.update(message_category, {"category": category})
        else:
            new_message_category = self.init_resource(
                "message_category",
                {
                    "resource": resource,
                    "resource_id": resource_id,
                    "category": category,
                },
            )
            await self.statemgr.insert(new_message_category)

    @action(
        "message-category-remove",
        resources=("message", "message_recipient", "message_category"),
    )
    async def remove_message_category(self, *, resource: str, resource_id: str):
        """Action to remove the category of a message."""
        message_category = await self.statemgr.find_one(
            "message_category",
            {
                "resource": resource,
                "resource_id": resource_id,
            },
        )
        await self.statemgr.invalidate(message_category)
