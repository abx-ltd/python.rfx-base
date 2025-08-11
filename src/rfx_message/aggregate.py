"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR, timestamp
from typing import Optional, Dict, Any
import asyncio

from .processor import MessageContentProcessor
from .types import MessageType, RenderingStrategy, ProcessingMode
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
        message_data = serialize_mapping(data)
        message_data['render_status'] = 'pending'
        
        message = self.init_resource(
            "message",
            message_data,
            _id=self.aggroot.identifier
        )
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
        
        processing_mode = ProcessingMode(mode)
        
        # Process content
        processed_message = await self.content_processor.process_message_content(
            message.__dict__,
            mode=processing_mode,
            context=context or {}
        )
        
        return {
            "message_id": message_id,
            "render_status": processed_message['render_status'],
            "content_type": processed_message.get('content_type'),
        }
    
    @action("message-ready-for-delivery", resources="message")
    async def mark_ready_for_delivery(self, *, message_id: str):
        """Mark message as ready for delivery."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")
        
        # Check if message is rendered or ready for client rendering
        if message.render_status not in ['rendered', 'ready_client_render']:
            raise ValueError(f"Message {message_id} is not ready for delivery (status: {message.render_status})")
        
        await self.statemgr.update(message, delivery_status='ready')
        
        return {"message_id": message_id, "ready": True}

    @action("recipients-added", resources="message-recipient")
    async def add_recipients(self, *, data, message_id):
        """Action to add recipients to a message."""
        recipients = data if isinstance(data, list) else data.get("recipients", [])
        
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": False,
                "delivered": False,
                "delivery_status": "pending"
            }
            
            recipient = self.init_resource("message-recipient", recipient_data)
            await self.statemgr.insert(recipient)
        
        return {
            "message_id": message_id,
            "recipients_count": len(recipients)
        }

    @action("message-read", resources="message-recipient")
    async def mark_message_read(self, *, message_id, user_id):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record
        recipient = await self.statemgr.find_one(
            "message-recipient",
            where={"message_id": message_id, "recipient_id": user_id}
        )
        
        if not recipient:
            raise ValueError(f"Recipient not found: {user_id} for message {message_id}")
        
        await self.statemgr.update(recipient, 
                                 read=True, 
                                 read_at=timestamp())
        
        return {
            "message_id": message_id,
            "user_id": user_id,
            "read": True
        }

    @action("all-messages-read", resources="message-recipient")
    async def mark_all_messages_read(self, *, user_id):
        """Action to mark all messages as read for a user."""
        recipients = await self.statemgr.find_many(
            "message-recipient",
            where={"recipient_id": user_id, "read": False}
        )
        
        updated_count = 0
        for recipient in recipients:
            await self.statemgr.update(recipient, 
                                     read=True, 
                                     read_at=timestamp())
            updated_count += 1
        
        return {
            "user_id": user_id,
            "updated_count": updated_count
        }

    @action("message-archived", resources="message-recipient")
    async def archive_message(self, *, message_id, user_id):
        """Action to archive a message for a specific user."""
        recipient = await self.statemgr.find_one(
            "message-recipient",
            where={"message_id": message_id, "recipient_id": user_id}
        )
        
        if not recipient:
            raise ValueError(f"Recipient not found: {user_id} for message {message_id}")
        
        await self.statemgr.update(recipient, 
                                 archived=True, 
                                 archived_at=timestamp())
        
        return {
            "message_id": message_id,
            "user_id": user_id,
            "archived": True
        }

    # ========================================================================
    # TEMPLATE OPERATIONS
    # ========================================================================

    @action("template-created", resources="message-template")
    async def create_template(self, *, data):
        """Create a new message template."""
        template_data = serialize_mapping(data)
        template = self.init_resource("message-template", template_data)
        await self.statemgr.insert(template)
        
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
        
        await self.statemgr.update(template,
                                 status="published",
                                 updated_by=published_by)
        
        # Invalidate cache if using content processor
        if hasattr(self, '_content_processor') and self._content_processor:
            await self._content_processor.template_service.invalidate_template_cache(
                template.key, template.version
            )
        
        return {
            "template_id": template_id,
            "key": template.key,
            "version": template.version,
            "status": "published"
        }