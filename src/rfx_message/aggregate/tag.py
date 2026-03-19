from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from uuid import UUID


class TagMixin:
    @action("tag-find")
    async def find_tag(self, *, tag_id: UUID):
        """Find a tag."""
        tag = await self.statemgr.find_one(
            "tag",
            where=dict(_id=tag_id),
        )
        return tag

    @action("tag-created", resources="tag")
    async def create_tag(self, *, data):
        """Create a new tag."""
        tag = self.init_resource(
            "tag",
            serialize_mapping(data),
            _id=UUID_GENR(),
            profile_id=self.get_context().profile_id,
        )
        await self.statemgr.insert(tag)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, *, data):
        """Update a tag."""
        tag = self.rootobj
        await self.statemgr.update(tag, **serialize_mapping(data))

    @action("tag-removed", resources="tag")
    async def remove_tag(self):
        """Remove a tag."""
        tag = self.rootobj
        await self.statemgr.invalidate(tag)
