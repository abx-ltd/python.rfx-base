from fluvius.domain.aggregate import action

from ..types import (
    MessageCategoryEnum,
)


class MessageCategoryMixin:
    @action("update-message-category", resources="message")
    async def update_message_category(self, *, category: MessageCategoryEnum):
        message = self.rootobj
        await self.statemgr.update(message, category=category)

    @action("remove-message-category", resources="message")
    async def remove_message_category(self):
        message = self.rootobj
        await self.statemgr.update(message, category=None)
