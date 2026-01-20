from fluvius.domain.aggregate import action


class MessageBoxMixin:
    @action("message-box-view-get", resources="message")
    async def get_message_box_view(self, message_id):
        """Get message box record."""
        return await self.statemgr.find_one(
            "_message_box",
            where={
                "message_id": message_id,
                "target_profile_id": self.context.profile_id,
            },
        )

    @action("sender-box-changed", resources="message")
    async def change_sender_box_id(self, /, message_id, box_id):
        """Change box_id for message_sender."""
        message_sender = await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id},
        )
        await self.statemgr.update(message_sender, box_id=box_id)

    @action("recipient-box-changed", resources="message")
    async def change_recipient_box_id(self, /, message_id, box_id):
        """Change box_id for message_recipient."""
        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id},
        )
        await self.statemgr.update(message_recipient, box_id=box_id)

    @action("message-box-get", resources="message")
    async def get_message_box(self, box_key):
        """Get message box."""
        return await self.statemgr.find_one(
            "message_box",
            where={"key": box_key},
        )
