from .domain import RFXMediaDomain

processor = RFXMediaDomain.command_processor
Command = RFXMediaDomain.Command


class RemoveMedia(Command):
    """Remove Media - Removes a media entry"""

    class Meta:
        key = "remove-media"
        resources = ("media-entry",)
        tags = ["media", "remove"]
        auth_required = True
        description = "Remove media entry"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Remove media entry"""
        await agg.remove_media()
