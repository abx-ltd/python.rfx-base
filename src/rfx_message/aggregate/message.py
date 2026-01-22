from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional, Dict, Any

from ..types import (
    ProcessingModeEnum,
    RenderStatusEnum,
    MessageCategoryEnum,
)


class MessageMixin:
    @action("message-generated", resources="message")
    async def generate_message(self, *, data, sender_id):
        """Action to create a new message."""
        message_data = data
        message_data["render_status"] = "PENDING"

        message = self.init_resource(
            "message",
            message_data,
            _id=UUID_GENR(),
            sender_id=sender_id,
            thread_id=UUID_GENR(),
        )

        await self.statemgr.insert(message)

        return message

    @action("message-replied", resources="message")
    async def reply_message(self, *, data):
        """Action to reply to a message."""
        message = self.rootobj
        reply_message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=UUID_GENR(),
            thread_id=message.thread_id,
            sender_id=self.context.profile_id,
            parent_id=message._id,
        )

        await self.statemgr.insert(reply_message)

        return reply_message

    @action("message-content-processed", resources="message")
    async def process_message_content(
        self,
        *,
        message_id: str,
        context: Optional[Dict[str, Any]] = None,
        mode: str = "sync",
    ):
        """Process message content (template resolution and rendering)."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        processing_mode = ProcessingModeEnum(mode)

        # Process content
        processed_message = await self.content_processor.process_message_content(
            message, mode=processing_mode, context=context or {}
        )

        return processed_message

    @action("message-ready-for-delivery", resources="message")
    async def mark_ready_for_delivery(self, message_id):
        """Mark message as ready for delivery."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        if message.render_status.value not in [
            RenderStatusEnum.COMPLETED.value,
            RenderStatusEnum.CLIENT_RENDERING.value,
        ]:
            raise ValueError(
                f"Message {message_id} is not ready for delivery (status: {message.render_status})"
            )

        await self.statemgr.update(message, delivery_status="PENDING")

        return {"message_id": message_id, "status": "PENDING"}

    # @action("get-all-message-in-thread-from-message", resources="message")
    # async def get_all_message_view_in_thread_from_message(self, message_id):
    #     """Get all messages in a thread."""
    #     message = self.rootobj
    #     return await self.statemgr.find_all(
    #         "_message_box",
    #         where={"thread_id": message.thread_id},
    #     )

    @action("change-all-sender-box-id-of-same-thread", resources="message")
    async def change_all_sender_box_id_of_same_thread(self, box_id, profile_id):
        """Change all sender box id of same thread."""

        message = self.rootobj
        messages = await self.statemgr.find_all(
            "message",
            where={"thread_id": message.thread_id},
        )
        for message in messages:
            sender = await self.statemgr.exist(
                "message_sender",
                where={"message_id": message._id, "sender_id": profile_id},
            )
            if sender:
                await self.statemgr.update(sender, box_id=box_id)

    @action("change-all-recipient-box-id-of-same-thread", resources="message")
    async def change_all_recipient_box_id_of_same_thread(self, box_id, profile_id):
        """Change all recipient box id of same thread."""
        message = self.rootobj
        messages = await self.statemgr.find_all(
            "message",
            where={"thread_id": message.thread_id},
        )
        for message in messages:
            recipient = await self.statemgr.exist(
                "message_recipient",
                where={"message_id": message._id, "recipient_id": profile_id},
            )
            if recipient:
                await self.statemgr.update(recipient, box_id=box_id)

