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

        # If message has direct content, no template rendering needed
        if message.content:
            await self.statemgr.update(
                message,
                render_status=RenderStatusEnum.COMPLETED.value
            )
            return serialize_mapping(message)

        # If message has template_key, render via rfx-template domain
        if message.template_key:
            try:
                template_client = self.context.service_proxy.ttp_client

                # Call rfx-template:render-template
                response = await template_client.request(
                    "rfx-template:render-template",
                    command="render-template",
                    resource="template",
                    payload={
                        "key": message.template_key,
                        "data": context or {},
                        "tenant_id": str(self.context.tenant_id) if hasattr(self.context, 'tenant_id') else None,
                        "app_id": getattr(self.context, 'app_id', None),
                        "locale": message.locale or "en",
                        "channel": message.channel,
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(self.context.user_id) if self.context.user_id else None,
                            "profile_id": str(self.context.profile_id) if self.context.profile_id else None,
                        },
                        "source": "rfx-message",
                    },
                )

                # Extract rendered content from template-service-response
                service_response = response.get("template-service-response", response)
                rendered_content = service_response.get('body', '')

                # Update message with rendered content
                await self.statemgr.update(
                    message,
                    content=rendered_content,
                    render_status=RenderStatusEnum.COMPLETED.value
                )

                # Refetch updated message
                message = await self.statemgr.fetch("message", message_id)

            except Exception as e:
                # Mark rendering as failed
                await self.statemgr.update(
                    message,
                    render_status=RenderStatusEnum.FAILED.value,
                    render_error=str(e)
                )
                raise ValueError(f"Template rendering failed: {str(e)}")

        return serialize_mapping(message)

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

