"""
Commands for the RFX messaging domain.
"""

from fluvius.domain.command import Command
from fluvius.data import serialize_mapping, UUID_GENR
import asyncio

from .domain import MessageServiceDomain
from .processor import ProcessingMode
from .helper import RenderingStrategy, extract_template_context
from .types import MessageType
from . import datadef
from . import logger

class SendMessage(Command):
    """
    Send a notification message to recipients.
    
    Supports both template-based and direct content messages.
    """
    
    async def _process(self, agg, stm, payload):
        try:
            # Validate payload
            if not (payload.get('template_key') or payload.get('content')):
                raise ValueError("Either 'template_key' or 'content' must be provided")
            
            if not payload.get('recipients'):
                raise ValueError("Recipients list cannot be empty")
            
            # 1. Create message record
            message_result = await agg.generate_message(data=serialize_mapping(payload))
            message_id = message_result["message_id"]
            
            # 2. Add recipients
            await agg.add_recipients(
                data=payload['recipients'],
                message_id=message_id
            )
            
            # 3. Determine processing mode
            message_type = MessageType(payload.get('message_type', 'NOTIFICATION'))
            processing_mode = self._determine_processing_mode(message_type, payload)
            
            # 4. Process content
            if processing_mode == ProcessingMode.SYNC:
                # Process immediately (blocking)
                await agg.process_message_content(
                    message_id=message_id,
                    context=extract_template_context(payload),
                    mode=processing_mode.value
                )
                
                # Mark ready for delivery
                await agg.mark_ready_for_delivery(message_id=message_id)
                
                # Send notification immediately
                await self._send_notification(message_id, payload)
                
            elif processing_mode == ProcessingMode.IMMEDIATE:
                # Critical alerts - process sync but with high priority
                await agg.process_message_content(
                    message_id=message_id,
                    context=extract_template_context(payload),
                    mode="sync"
                )
                
                await agg.mark_ready_for_delivery(message_id=message_id)
                await self._send_notification(message_id, payload, priority=True)
                
            else:  # ASYNC
                # Process in background
                asyncio.create_task(
                    self._process_async(agg, message_id, payload)
                )
            
            yield agg.create_response({
                "status": "success",
                "message_id": message_id,
                "processing_mode": processing_mode.value,
                "recipients_count": len(payload['recipients'])
            }, _type="message-service-response")
            
        except Exception as e:
            logger.error(f"SendMessage failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="message-service-response")
            raise
    
    def _determine_processing_mode(self, message_type: MessageType, payload: dict) -> ProcessingMode:
        """Determine how to process the message based on type and content."""
        
        # Direct content can be processed immediately
        if payload.get('content'):
            return ProcessingMode.SYNC
        
        # Critical alerts are always immediate
        if message_type == MessageType.ALERT:
            return ProcessingMode.IMMEDIATE
        
        # High priority messages
        if payload.get('priority') == 'high':
            return ProcessingMode.SYNC
        
        # Template-based messages with client rendering can be fast
        strategy = payload.get('render_strategy')
        if strategy == RenderingStrategy.CLIENT.value:
            return ProcessingMode.SYNC
        
        # Default to async for complex rendering
        return ProcessingMode.ASYNC
    
    async def _process_async(self, agg, message_id: str, payload: dict):
        """Process message content asynchronously."""
        try:
            await agg.process_message_content(
                message_id=message_id,
                context=extract_template_context(payload),
                mode="async"
            )
            
            await agg.mark_ready_for_delivery(message_id=message_id)
            await self._send_notification(message_id, payload)
            
        except Exception as e:
            logger.error(f"Async message processing failed for {message_id}: {e}")
            # TODO: Could retry or send to dead letter queue
    
    async def _send_notification(self, message_id: str, payload: dict, priority: bool = False):
        """Send notification via MQTT."""
        try:
            # Get the framework MQTT client
            mqtt_client = self.framework.mqtt_client
            
            if not mqtt_client:
                logger.warning("MQTT client not available, skipping notification")
                return
            
            # Send notification to each recipient
            for recipient_id in payload['recipients']:
                await mqtt_client.notify(
                    user_id=recipient_id,
                    kind="message",
                    target="inbox",
                    msg={
                        "message_id": message_id,
                        "subject": payload.get('subject', 'New notification'),
                        "message_type": payload.get('message_type', 'NOTIFICATION'),
                        "priority": payload.get('priority', 'normal'),
                        "timestamp": payload.get('_created'),
                        "urgent": priority
                    }
                )
            
            logger.info(f"Notification sent for message {message_id} to {len(payload['recipients'])} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send notification for message {message_id}: {e}")

class ReadMessage(Command):
    """Mark a message as read for the current user."""
    
    async def _process(self, agg, stm, payload):
        user_id = self.context.user._id
        message_id = payload.message_id
        
        await agg.mark_message_read(
            message_id=message_id,
            user_id=user_id
        )
        
        # Send status update via MQTT
        mqtt_client = self.framework.mqtt_client
        if mqtt_client:
            await mqtt_client.notify(
                user_id=user_id,
                kind="status",
                target="read",
                msg={
                    "message_id": message_id,
                    "action": "read",
                    "timestamp": payload.get('_created')
                }
            )
        
        yield agg.create_response({
            "status": "success",
            "message_id": message_id,
        }, _type="message-service-response")

class MarkAllMessagesRead(Command):
    """Mark all messages as read for the current user."""
    
    async def _process(self, agg, stm, payload):
        user_id = self.context.user._id
        
        result = await agg.mark_all_messages_read(user_id=user_id)
        
        # Send status update via MQTT
        mqtt_client = self.framework.mqtt_client
        if mqtt_client:
            await mqtt_client.notify(
                user_id=user_id,
                kind="status",
                target="bulk_read",
                msg={
                    "action": "mark_all_read",
                    "count": result["updated_count"],
                    "timestamp": payload.get('_created')
                }
            )
        
        yield agg.create_response({
            "status": "success",
            "updated_count": result["updated_count"],
        }, _type="message-service-response")

class ArchiveMessage(Command):
    """Archive a message for the current user."""
    
    async def _process(self, agg, stm, payload):
        user_id = self.context.user._id
        message_id = payload.message_id
        
        await agg.archive_message(
            message_id=message_id,
            user_id=user_id
        )
        
        yield agg.create_response({
            "status": "success",
            "message_id": message_id,
        }, _type="message-service-response")

# Template management commands
class CreateTemplate(Command):
    """Create a new message template."""
    
    async def _process(self, agg, stm, payload):
        result = await agg.create_template(data=serialize_mapping(payload))
        
        yield agg.create_response({
            "status": "success",
            "template_id": result["template_id"],
            "key": result["key"],
            "version": result["version"]
        }, _type="template-service-response")

class PublishTemplate(Command):
    """Publish a template to make it available."""
    
    async def _process(self, agg, stm, payload):
        result = await agg.publish_template(
            template_id=payload.template_id,
            published_by=self.context.user._id
        )
        
        yield agg.create_response({
            "status": "success",
            "template_id": result["template_id"],
            "key": result["key"],
            "version": result["version"],
            "status": result["status"]
        }, _type="template-service-response")