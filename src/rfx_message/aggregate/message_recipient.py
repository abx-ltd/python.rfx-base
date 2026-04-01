from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping


class MessageRecipientMixin:
    @action("get-message-recipient", resources="message")
    async def get_message_recipient(self, message_id, profile_id):
        """Get message recipient."""
        return await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )

    @action("remove-message-recipient", resources="message")
    async def remove_message_recipient(self, message_id, profile_id):
        """Remove message recipient."""

        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )
        await self.statemgr.invalidate(message_recipient)

    @action("check-message-recipient", resources="message")
    async def check_message_recipient(self, message_id, profile_id):
        """Check if message recipient exists."""
        return await self.statemgr.exist(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )

    @action("recipients-added",resources=("message"),)
    async def add_recipients(self, *, data, message_id, sender=None, sender_result=None):
        """Add recipients to a message using the shared member box."""
        recipients = data or []
        if not recipients:
            return {"message_id": message_id, "recipients_count": 0}

        member_box_id = None
        if sender_result:
            member_box_id = sender_result.get("box_id")

        if not member_box_id:
            sender_id = sender or self.get_context().profile_id
            member_box = await self.get_or_create_member_box(sender_id, recipients)
            member_box_id = member_box._id

        records = []
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": self.get_context().profile_id == recipient_id,
                "box_id": member_box_id,
                "direction": "INBOUND",
            }

            recipient = self.init_resource("message_recipient", recipient_data)
            records.append(serialize_mapping(recipient))

        await self.statemgr.insert_data("message_recipient", *records)

        return {
            "message_id": message_id,
            "recipients_count": len(recipients),
            "box_id": member_box_id,
        }
