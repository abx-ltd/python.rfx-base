from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping


class MessageRecipientMixin:
    @action("remove-message-recipient", resources="message")
    async def remove_message_recipient(self, message_id):
        """Remove message recipient."""

        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": self.context.profile_id},
        )
        await self.statemgr.invalidate(message_recipient)

    @action("check-message-recipient", resources="message")
    async def check_message_recipient(self, message_id):
        """Check if message recipient exists."""
        return await self.statemgr.exist(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": self.context.profile_id},
        )

    @action("recipients-added", resources=("message", "message_recipient"))
    async def add_recipients(self, *, data, message_id):
        """Action to add recipients to a message."""
        recipients = data
        # Get the inbox box
        inbox = await self.statemgr.find_one(
            "message_box",
            where={"key": "inbox"},
        )

        records = []
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": False,
                "box_id": inbox._id,
                "direction": "INBOUND",
            }

            recipient = self.init_resource("message_recipient", recipient_data)
            records.append(serialize_mapping(recipient))

        await self.statemgr.insert_data("message_recipient", *records)

        return {"message_id": message_id, "recipients_count": len(recipients)}
