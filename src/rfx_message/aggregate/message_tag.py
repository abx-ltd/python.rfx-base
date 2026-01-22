from fluvius.domain.aggregate import action


class MessageTagMixin:
    @action("message-tag-added", resources="message")
    async def add_message_tag(self, *, resource: str, resource_id: str, key: str):
        """Action to add a tag to a message."""
        existing_tag = await self.statemgr.exist(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "key": key},
        )
        if existing_tag:
            return

        message_tag = self.init_resource(
            "message_tag",
            {
                "resource": resource,
                "resource_id": resource_id,
                "key": key,
            },
        )
        await self.statemgr.insert(message_tag)

    @action("message-tag-removed", resources="message")
    async def remove_message_tag(self, *, resource: str, resource_id: str, key: str):
        """Action to remove a tag from a message."""
        message_tag = await self.statemgr.find_one(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "key": key},
        )
        await self.statemgr.invalidate(message_tag)

    @action("message-tag-remove-all", resources="message")
    async def remove_all_message_tags(self, *, resource: str, resource_id: str):
        """Action to remove all tags from a message."""
        message_tags = await self.statemgr.find_all(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id},
        )
        for message_tag in message_tags:
            await self.statemgr.invalidate(message_tag)