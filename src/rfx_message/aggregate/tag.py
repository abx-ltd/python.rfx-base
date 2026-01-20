from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
 

class TagMixin:
    @action("tag-created", resources="tag")
    async def create_tag(self, *, data):
        """Create a new tag."""
        tag = self.init_resource("tag", serialize_mapping(data), _id=UUID_GENR())
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
