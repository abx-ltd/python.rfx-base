"""
Message content processor for handling template resolution and rendering.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

from fluvius.data import DataAccessManager, timestamp, DataModel, serialize_mapping
from .service import TemplateService
from .helper import render_on_server, extract_template_context, message_to_notification_data
from .types import MessageTypeEnum, RenderStrategyEnum, ProcessingModeEnum
from .datadef import Notification
from . import logger

class MessageContentProcessor:
    """Handles message content resolution and rendering."""
    
    def __init__(self, stm: DataAccessManager):
        self.stm = stm
        self.template_service = TemplateService(stm)

    async def process_message_content(
        self,
        message: DataModel,
        *,
        mode: ProcessingModeEnum = ProcessingModeEnum.SYNC,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process message content based on type and strategy.
        
        Flow:
        1. Check if direct content is provided (no template needed)
        2. Resolve template if template_key is provided
        3. Determine rendering strategy
        4. Render content or prepare for client rendering
        5. Update message with processed content
        6. Fetch updated message and convert to Notification
        """
        try:
            # If direct content is provided, use it as-is
            if message.content:
                updated_message = await self._process_direct_content(message)
            # Template-based content processing
            elif message.template_key:
                updated_message = await self._process_template_content(message, context or {})
            
            # Fetch the updated message to ensure we have the latest data
            fresh_message = await self.stm.fetch("message", message._id)
            if not fresh_message:
                raise ValueError(f"Message not found after processing: {message._id}")
            
            # Convert to Notification model
            return serialize_mapping(message_to_notification_data(fresh_message))
            
        except Exception as e:
            logger.error(f"Content processing failed for message {message._id}: {e}")
            await self._mark_processing_failed(message, str(e))
            raise

    async def _process_direct_content(self, message: DataModel) -> DataModel:
        """Process message with direct content (no template)."""
        content = message.content
        content_type = getattr(message, 'content_type', 'text/plain')
        
        # Update message status - use timezone-aware datetime
        await self.stm.update(
            message,
            rendered_content=content,
            content_type=content_type,
            render_status='COMPLETED',
            rendered_at=datetime.utcnow()
        )
        
        logger.debug(f"Processed direct content for message {message._id}")
        return message
    
    async def _process_template_content(
        self,
        message: DataModel,
        context: Dict[str, Any]
    ) -> DataModel:
        """Process message with template-based content."""
        
        # Extract template resolution context - access attributes properly
        template_context = extract_template_context(message, **context)
        
        # Resolve template
        template = await self.template_service.resolve_template(
            message.template_key,
            **template_context,
            version=getattr(message, 'template_version', None)
        )
        
        if not template:
            raise ValueError(f"Template not found: {message.template_key}")
        
        # Determine rendering strategy
        message_type = MessageTypeEnum(getattr(message, 'message_type', 'NOTIFICATION'))
        strategy = await self.template_service.resolve_render_strategy(
            message_type,
            message_strategy=RenderStrategyEnum(message.render_strategy) if getattr(message, 'render_strategy', None) else None,
            template_strategy=RenderStrategyEnum(template.render_strategy) if getattr(template, 'render_strategy', None) else None
        )

        logger.debug(f"Using rendering strategy: {strategy.value} for message {message._id}")

        # Process based on strategy
        if render_on_server(strategy):
            return await self._render_on_server(message, template, strategy)
        else:
            return await self._prepare_for_client_render(message, template)
    
    async def _render_on_server(
        self,
        message: DataModel,
        template: DataModel,
        strategy: RenderStrategyEnum
    ) -> DataModel:
        """Render template on server and store result."""
        
        # Get template data - use attribute access
        template_data = getattr(message, 'template_data', {}) or {}
        
        # Add system variables
        template_data.update({
            'message_id': message._id,
            'timestamp': datetime.utcnow().isoformat(),  # Use timezone-aware datetime for ISO format
            'sender_id': getattr(message, 'sender_id', None),
            # Add more system variables as needed
        })
        
        # Render template
        use_cache = (strategy == RenderStrategyEnum.CACHED)
        rendered_content = await self.template_service.render_template(
            template,
            template_data,
            use_cache=use_cache
        )
        
        # Determine content type based on engine
        content_type = self._get_content_type_for_engine(getattr(template, 'engine', 'jinja2'))
        
        # Update message with rendered content - use timezone-aware datetime
        await self.stm.update(
            message,
            rendered_content=rendered_content,
            content_type=content_type,
            template_version=template.version,
            template_locale=template.locale,
            template_engine=template.engine,
            render_status='COMPLETED',
            rendered_at=datetime.utcnow()  # Use timezone-aware datetime
        )

        logger.info(f"Server-rendered message {message._id} using template {template.key} v{template.version}")

        return message
    
    async def _prepare_for_client_render(
        self,
        message: DataModel,
        template: DataModel
    ) -> DataModel:
        """Prepare message for client-side rendering."""
        
        # Store template reference for client - use timezone-aware datetime
        await self.stm.update(
            message,
            template_version=template.version,
            template_locale=template.locale,
            template_engine=template.engine,
            render_status='CLIENT_RENDERING',
            rendered_at=datetime.utcnow()  # Use timezone-aware datetime
        )
        
        logger.info(f"Prepared message {message._id} for client rendering using template {template.key} v{template.version}")
        
        return message
    
    async def _mark_processing_failed(self, message: DataModel, error: str):
        """Mark message processing as failed."""
        await self.stm.update(
            message,
            render_status='FAILED',
            render_error=error,
            rendered_at=datetime.utcnow()  # Use timezone-aware datetime
        )
    
    def _get_content_type_for_engine(self, engine: str) -> str:
        """Get appropriate content type for template engine."""
        engine_content_types = {
            'jinja2': 'text/html',
            'markdown': 'text/html',
            'txt': 'text/plain',
            'static': 'text/plain'
        }
        return engine_content_types.get(engine, 'text/plain')
    
    async def retry_failed_processing(self, message_id: str, recipient_id: str) -> Notification:
        """Retry processing for a failed message."""
        message = await self.stm.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")
        
        if getattr(message, 'render_status', None) != 'FAILED':
            raise ValueError(f"Message {message_id} is not in failed state")
        
        # Reset status and retry - use timezone-aware datetime
        await self.stm.update(message, render_status='PENDING', render_error=None)
        return await self.process_message_content(message, recipient_id)