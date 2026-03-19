from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action


class RFXMediaAggregate(Aggregate):
    @action("media-removed", resources="media-entry")
    async def remove_media(self):
        """Action to remove a media entry."""
        media_entry = self.rootobj
        await self.statemgr.invalidate(media_entry)
