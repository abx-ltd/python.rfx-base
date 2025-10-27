"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from unittest import result
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR, timestamp
from typing import Optional, Dict, Any
# import asyncio

from .processor import MessageContentProcessor
from .types import MessageTypeEnum, RenderStrategyEnum, ProcessingModeEnum, RenderStatusEnum
from . import logger

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_processor = None

    @property
    def content_processor(self) -> MessageContentProcessor:
        """Lazy-loaded content processor."""
        if self._content_processor is None:
            self._content_processor = MessageContentProcessor(self.statemgr)
        return self._content_processor

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-generated", resources="message")
    async def generate_message(self, *, data):
        """Action to create a new message."""
        message_data = data
        message_data['render_status'] = 'PENDING'

        message = self.init_resource("message", message_data, _id=self.aggroot.identifier)
        await self.statemgr.insert(message)

        return {
            "message_id": message._id,
        }

    @action("message-content-processed", resources="message")
    async def process_message_content(
        self,
        *,
        message_id: str,
        context: Optional[Dict[str, Any]] = None,
        mode: str = "sync"
    ):
        """Process message content (template resolution and rendering)."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        processing_mode = ProcessingModeEnum(mode)

        # Process content
        processed_message = await self.content_processor.process_message_content(
            message,
            mode=processing_mode,
            context=context or {}
        )

        return processed_message

    @action("message-ready-for-delivery", resources="message")
    async def mark_ready_for_delivery(self, message_id):
        """Mark message as ready for delivery."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        # Check if message is rendered or ready for client rendering
        # Compare against enum values
        if message.render_status not in [RenderStatusEnum.COMPLETED, RenderStatusEnum.CLIENT_RENDERING]:
            raise ValueError(f"Message {message_id} is not ready for delivery (status: {message.render_status})")

        await self.statemgr.update(message, delivery_status='PENDING')

        return {"message_id": message_id, "status": "PENDING"}

    @action("recipients-added", resources=("message", "message-recipient"))
    async def add_recipients(self, *, data, message_id):
        """Action to add recipients to a message."""
        recipients = data
        records = []
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": False,
            }

            recipient = self.init_resource("message-recipient", recipient_data)
            records.append(serialize_mapping(recipient))

        await self.statemgr.insert_many("message-recipient", *records)

        return {
            "message_id": message_id,
            "recipients_count": len(recipients)
        }

    @action("message-read", resources="message-recipient")
    async def mark_message_read(self):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record
        recipient = await self.statemgr.fetch("message-recipient", self.aggroot.identifier)

        if not recipient:
            raise ValueError(f"Recipient not found: {self.aggroot.identifier}")

        await self.statemgr.update(recipient, read=True, mark_as_read=timestamp())

    @action("all-messages-read", resources="message-recipient")
    async def mark_all_messages_read(self):
        """Action to mark all messages as read for a user."""
        user_id = self.context.user_id
        recipients = await self.statemgr.find_all(
            "message-recipient",
            where={"recipient_id": user_id, "read": False}
        )

        updated_count = 0
        for recipient in recipients:
            await self.statemgr.update(recipient, read=True, mark_as_read=timestamp())
            updated_count += 1

        return {
            "user_id": user_id,
            "updated_count": updated_count
        }

    @action("message-archived", resources="message-recipient")
    async def archive_message(self):
        """Action to archive a message for a specific user."""
        message_id = self.aggroot.identifier

        recipient = await self.statemgr.fetch("message-recipient", message_id)
        if not recipient:
            raise ValueError(f"Recipient not found: {self.context.user_id} for message {message_id}")

        await self.statemgr.update(recipient, archived=True, archived_at=timestamp())

        return message_id

    # ========================================================================
    # TEMPLATE OPERATIONS
    # ========================================================================

    @action("template-created", resources="message-template")
    async def create_template(self, *, data):
        """Create a new message template."""
        template_data = serialize_mapping(data)

        old_template = self.statemgr.find_one(
            "message-template",
            where=dict(
                tenant_id=getattr(data, 'tenant_id', None),
                app_id=getattr(data, 'app_id', None),
                key=getattr(data, 'key', None),
                locale=getattr(data, 'locale', None),
                channel=getattr(data, 'channel', None)
            )
        )

        if old_template:
            template_data['version'] = old_template.version + 1
        else:
            template_data['version'] = 1

        template = self.init_resource("message-template", template_data, _id=self.aggroot.identifier)
        await self.statemgr.insert(template)

        return {
            "template_id": template._id,
            "key": template.key,
        }

    @action("template-updated", resources="message-template")
    async def update_template(self, *, data):
        """Update an existing message template."""
        template = self.statemgr.fetch("message-template", self.aggroot.identifier)
        if template:
            return ValueError(f"Template not found: {self.aggroot.identifier}")

        await self.statemgr.update(template, **data)

        return {
            "template_id": template._id,
            "key": template.key,
            "version": template.version
        }

    @action("template-published", resources="message-template")
    async def publish_template(self, *, template_id, published_by=None):
        """Publish a template to make it available for use."""
        template = await self.statemgr.fetch("message-template", template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        await self.statemgr.update(template, status="PUBLISHED", updated_by=published_by)

        # Invalidate cache if using content processor
        if hasattr(self, '_content_processor') and self._content_processor:
            await self._content_processor.template_service.invalidate_template_cache(
                template.key, template.version
            )

        return {
            "template_id": template_id,
            "key": template.key,
            "version": template.version,
            "status": "PUBLISHED"
        }
