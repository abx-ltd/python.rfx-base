from fluvius.domain.aggregate import action
from fluvius.data import UUID_GENR, serialize_mapping


class MessageSenderMixin:
    def _normalize_member_ids(self, sender_id, recipients=None):
        """Build a unique ordered member list from sender and recipients."""
        member_ids = [sender_id, *(recipients or [])]
        return [member_id for member_id in dict.fromkeys(member_ids) if member_id]

    async def find_members_by_box_id(self, box_id, member_ids):
        """Check whether the box contains exactly the requested members."""
        memberships = await self.statemgr.find_all(
            "message_box_user",
            where={"box_id": box_id},
        )
        box_member_ids = {membership.user_id for membership in memberships}
        return box_member_ids == set(member_ids)

    async def get_or_create_member_box(self, sender_id, recipients=None):
        """Get an existing exact-match member box or create a new one."""
        unique_member_ids = self._normalize_member_ids(sender_id, recipients)

        sender_box_users = await self.statemgr.find_all(
            "message_box_user",
            where={"user_id": sender_id},
        )

        for box_user in sender_box_users:
            if await self.find_members_by_box_id(box_user.box_id, unique_member_ids):
                return await self.statemgr.find_one(
                    "message_box",
                    where={"_id": box_user.box_id},
                )

        box_type = "GROUP" if len(unique_member_ids) >= 2 else "SINGLE"
        box = self.init_resource(
            "message_box",
            {"name": None, "key": None, "type": box_type},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(box)

        box_users = []
        for member_id in unique_member_ids:
            box_user = self.init_resource(
                "message_box_user",
                {"user_id": member_id, "box_id": box._id},
                _id=UUID_GENR(),
            )
            box_users.append(serialize_mapping(box_user))

        await self.statemgr.insert_data("message_box_user", *box_users)
        return box

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
