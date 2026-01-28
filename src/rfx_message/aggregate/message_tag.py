from fluvius.domain.aggregate import action
from typing import List
from fluvius.data import UUID_TYPE


class MessageTagMixin:
    @action("message-tag-added", resources="message")
    async def add_message_tag(
        self, *, resource: str, resource_id: str, tag_id: UUID_TYPE
    ):
        """Action to add a tag to a message."""
        existing_tag = await self.statemgr.exist(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "tag_id": tag_id},
        )
        if existing_tag:
            return

        message_tag = self.init_resource(
            "message_tag",
            {
                "resource": resource,
                "resource_id": resource_id,
                "tag_id": tag_id,
            },
        )
        await self.statemgr.insert(message_tag)

    @action("message-tag-removed-from-resource", resources="message")
    async def remove_message_tag_from_resource(
        self, *, resource: str, resource_id: str, tag_id: UUID_TYPE
    ):
        """Action to remove a tag from a message."""
        message_tag = await self.statemgr.find_one(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "tag_id": tag_id},
        )
        await self.statemgr.invalidate(message_tag)

    @action("message-tag-remove-all-from-resource", resources="message")
    async def remove_all_message_tags_from_resource(
        self, *, resource: str, resource_id: str
    ):
        """Action to remove all tags from a message."""
        message_tags = await self.statemgr.find_all(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id},
        )
        for message_tag in message_tags:
            await self.statemgr.invalidate(message_tag)

    @action("message-tag-removed-from-tag", resources=("message", "tag"))
    async def remove_message_tag_from_tag(self, *, tag_id: UUID_TYPE):
        """Action to remove a tag from a message."""
        message_tags = await self.statemgr.find_all(
            "message_tag",
            where=dict(tag_id=tag_id),
        )
        for message_tag in message_tags:
            await self.statemgr.invalidate(message_tag)

    @action("message-tag-added-to-resource", resources="message")
    async def add_message_tags_to_resource(
        self, *, resource: str, resource_id: str, tag_ids: List[UUID_TYPE]
    ):
        """Action to add tags to a message."""
        for tag_id in tag_ids:
            await self.add_message_tag(
                resource=resource, resource_id=resource_id, tag_id=tag_id
            )
