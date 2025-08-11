"""
Commands for the RFX messaging domain.
"""

from fluvius.data import serialize_mapping, UUID_GENR
import asyncio

from .domain import MessageServiceDomain
from .helper import extract_template_context, determine_processing_mode
from .types import MessageType, ProcessingMode
from . import datadef, logger

processor = MessageServiceDomain.command_processor
Command = MessageServiceDomain.Command
class SendMessage(Command):
    """
    Send a notification message to recipients.
    
    Supports both template-based and direct content messages.
    """
    Data = datadef.SendMessagePayload

    class Meta:
        key = "send-message"
        new_resource = True
        resources = ("message",)
        tags = ["message"]
        auth_required = True
        policy_required = False

    
    async def process_message(self, agg, message_id, payload, mode):
        await agg.process_message_content(
            message_id=message_id,
            context=extract_template_context(payload),
            mode=mode
        )

        await agg.mark_ready_for_delivery(message_id)

    async def _process_async(self, agg, message_id: str, payload: dict):
        """Process message content asynchronously."""
        try:
            await self.process_message(agg, message_id, payload, "ASYNC")

        except Exception as e:
            logger.error(f"Async message processing failed for {message_id}: {e}")
            # TODO: Could retry or send to dead letter queue
        
    async def _process(self, agg, stm, payload):
        try:
            message_payload = serialize_mapping(payload)
            recipients = message_payload.pop("recipients", None)

            if not recipients:
                raise ValueError("Recipients list cannot be empty")
            
            # 1. Create message record
            message_result = await agg.generate_message(data=message_payload)
            message_id = message_result["message_id"]
            
            # 2. Add recipients
            await agg.add_recipients(data=recipients, message_id=message_id)
            
            # 3. Determine processing mode
            message_type = MessageType(message_payload.get('message_type', 'NOTIFICATION'))
            processing_mode = await determine_processing_mode(message_type=message_type, payload=message_payload)

            # 4. Process content
            if processing_mode == ProcessingMode.SYNC:
                # Process immediately (blocking)
                await self.process_message(agg, message_id, message_payload, processing_mode)

            elif processing_mode == ProcessingMode.IMMEDIATE:
                # Critical alerts - process sync but with high priority
                await self.process_message(agg, message_id, message_payload, "SYNC")
                
            else:
                # Process in background
                asyncio.create_task(
                    self._process_async(agg, message_id, message_payload)
                )
            
            yield agg.create_response({
                "status": "success",
                "message_id": message_id,
                "processing_mode": processing_mode.value,
                "recipients_count": len(recipients)
            }, _type="message-service-response")
            
        except Exception as e:
            logger.error(f"SendMessage failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="message-service-response")
            raise

class ReadMessage(Command):
    """Mark a message as read for the current user."""

    class Meta:
        key = "read-message"
        resources = ("message-recipient",)
        tags = ["message", "read"]
        auth_required = True
        policy_required = False
    
    async def _process(self, agg, stm, payload):
        
        await agg.mark_message_read()
        
        yield agg.create_response({
            "status": "success",
        }, _type="message-service-response")

class MarkAllMessagesRead(Command):
    """Mark all messages as read for the current user."""

    class Meta:
        key = "mark-all-message-read"
        # Substitute for the next Fluvius Batch update
        new_resource = True
        resources = ("message-recipient",)
        tags = ["messages", "read"]
        auth_required = True
        policy_required = False
    
    async def _process(self, agg, stm, payload):
        result = await agg.mark_all_messages_read()
        
        yield agg.create_response({
            "status": "success",
            "updated_count": result["updated_count"],
        }, _type="message-service-response")

class ArchiveMessage(Command):
    """Archive a message for the current user."""
    class Meta:
        key = "archive-message"
        resources = ("message-recipient",)
        tags = ["messages", "archived"]
        auth_required = True
        policy_required = False
    
    async def _process(self, agg, stm, payload):
        result = await agg.archive_message()
        
        yield agg.create_response({
            "status": "success",
            "message_id": result
        }, _type="message-service-response")

# Template management commands
class CreateTemplate(Command):
    """Create a new message template."""

    Data = datadef.CreateTemplatePayload
    class Meta:
        key = "create-template"
        new_resource = True
        resources = ("message-template",)
        tags = ["template", "create"]
        auth_required = True
        policy_required = False
    
    async def _process(self, agg, stm, payload):
        result = await agg.create_template(data=serialize_mapping(payload))
        
        yield agg.create_response({
            "status": "success",
            "template_id": result["template_id"],
            "key": result["key"],
        }, _type="message-service-response")

class UpdateTemplate(Command):
    """Update a template"""

    Data = datadef.CreateTemplatePayload

    class Meta:
        key = "update-template"
        resource = ("message-template")
        tags = ["template", "create"]
        auth_required = True
        policy_required = False
    
    async def _process(self, agg, stm, payload):
        result = await agg.update_template(data=serialize_mapping(payload))

        yield agg.create_response({
            "status": "success",
            "template_id": result["template_id"],
            "key": result["key"],
            "version": result["version"],
        }, _type="message-service-response")

class PublishTemplate(Command):
    """Publish a template to make it available."""

    Data = datadef.PublishTemplatePayload
    class Meta:
        key = "publish-template"
        resources = ("message-template",)
        tags = ["template", "publish"]
        auth_required = True
        policy_required = False
    
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
        }, _type="message-service-response")