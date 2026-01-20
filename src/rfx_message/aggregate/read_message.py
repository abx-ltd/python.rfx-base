from fluvius.domain.aggregate import action
from fluvius.data import timestamp


class ReadMessageMixin:
    @action("message-read", resources="message")
    async def mark_message_read(self):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record
        message = self.rootobj
        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message._id, "recipient_id": self.context.profile_id},
        )
        await self.statemgr.update(
            message_recipient, read=True, mark_as_read=timestamp()
        )

    @action("all-messages-read", resources="message")
    async def mark_all_messages_read(self):
        """Action to mark all messages as read for a user."""
        message_recipients = await self.statemgr.find_all(
            "message_recipient",
            where={"recipient_id": self.context.profile_id},
        )

        read_count = 0
        for recipient in message_recipients:
            await self.statemgr.update(recipient, read=True, mark_as_read=timestamp())
            if not recipient.read:
                read_count += 1
        return {"read_count": read_count}
