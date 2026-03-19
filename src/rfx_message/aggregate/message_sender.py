from fluvius.domain.aggregate import action


class MessageSenderMixin:
    @action("remove-message-sender", resources="message")
    async def remove_message_sender(self, message_id, profile_id):
        """Remove message sender."""
        message_sender = await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id, "sender_id": profile_id},
        )
        await self.statemgr.invalidate(message_sender)

    @action("check-message-sender", resources="message")
    async def check_message_sender(self, message_id, profile_id):
        """Check if message sender exists."""
        return await self.statemgr.exist(
            "message_sender",
            where={"message_id": message_id, "sender_id": profile_id},
        )

    @action("get-message-sender-by-message-id", resources="message")
    async def get_message_sender_by_message_id(self, message_id):
        """Get message sender by message id."""
        return await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id},
        )

    @action("get-message-sender", resources="message")
    async def get_message_sender(self, message_id, profile_id):
        """Get message sender."""
        return await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id, "sender_id": profile_id},
        )

    @action("sender-added", resources=("message", "message_sender"))
    async def add_sender(self, *, message_id, sender_id):
        """Action to add sender to a message."""
        # Get the outbox box
        outbox = await self.statemgr.find_one(
            "message_box",
            where={"key": "outbox"},
        )

        sender_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "box_id": outbox._id,
            "direction": "OUTBOUND",
        }

        sender = self.init_resource("message_sender", sender_data)
        await self.statemgr.insert(sender)

        return {"message_id": message_id, "sender_id": sender_id}
