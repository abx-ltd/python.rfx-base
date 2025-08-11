"""
Message content processor for handling template resolution and rendering.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from fluvius.data import DataAccessManager, timestamp
from .service import TemplateService
from .helper import render_on_server, extract_template_context
from .types import MessageType, RenderingStrategy, ProcessingMode
from . import logger



class MessageContentProcessor:
    """Handles message content resolution and rendering."""
    
    def __init__(self, stm: DataAccessManager):
        self.stm = stm
        self.template_service = TemplateService(stm)

    async def process_message_content(
        self,
        message: Dict[str, Any],
        *,
        mode: ProcessingMode = ProcessingMode.SYNC,
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
        """
        try:
            # If direct content is provided, use it as-is
            if message.get('content'):
                return await self._process_direct_content(message)
            
            # Template-based content processing
            if message.get('template_key'):
                return await self._process_template_content(message, context or {})
            
            # No content source provided
            raise ValueError("Message must have either 'content' or 'template_key'")
            
        except Exception as e:
            logger.error(f"Content processing failed for message {message.get('_id')}: {e}")
            await self._mark_processing_failed(message, str(e))
            raise
    
    async def _process_direct_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with direct content (no template)."""
        content = message['content']
        content_type = message.get('content_type', 'text/plain')
        
        # Update message status
        updates = {
            'rendered_content': content,
            'content_type': content_type,
            'render_status': 'rendered',
            'rendered_at': timestamp()
        }
        
        updated_message = await self.stm.update(message, **updates)
        logger.debug(f"Processed direct content for message {message['_id']}")
        
        return updated_message
    
    async def _process_template_content(
        self,
        message: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process message with template-based content."""
        
        # Extract template resolution context
        template_context = extract_template_context(message, **context)
        
        # Resolve template
        template = await self.template_service.resolve_template(
            message['template_key'],
            **template_context,
            version=message.get('template_version')
        )
        
        if not template:
            raise ValueError(f"Template not found: {message['template_key']}")
        
        # Determine rendering strategy
        message_type = MessageType(message.get('message_type', 'NOTIFICATION'))
        strategy = await self.template_service.resolve_render_strategy(
            message_type,
            message_strategy=RenderingStrategy(message['render_strategy']) if message.get('render_strategy') else None,
            template_strategy=RenderingStrategy(template['render_strategy']) if template.get('render_strategy') else None
        )
        
        logger.debug(f"Using rendering strategy: {strategy.value} for message {message['_id']}")
        
        # Process based on strategy
        if render_on_server(strategy):
            return await self._render_on_server(message, template, strategy)
        else:
            return await self._prepare_for_client_render(message, template)
    
    async def _render_on_server(
        self,
        message: Dict[str, Any],
        template: Dict[str, Any],
        strategy: RenderingStrategy
    ) -> Dict[str, Any]:
        """Render template on server and store result."""
        
        # Get template data
        template_data = message.get('template_data', {})
        
        # Add system variables
        template_data.update({
            'message_id': message['_id'],
            'timestamp': datetime.now().isoformat(),
            'sender_id': message.get('sender_id'),
            # Add more system variables as needed
        })
        
        # Render template
        use_cache = (strategy == RenderingStrategy.CACHED)
        rendered_content = await self.template_service.render_template(
            template,
            template_data,
            use_cache=use_cache
        )
        
        # Determine content type based on engine
        content_type = self._get_content_type_for_engine(template.get('engine', 'jinja2'))
        
        # Update message with rendered content
        updates = {
            'rendered_content': rendered_content,
            'content_type': content_type,
            'template_version': template['version'],
            'template_locale': template['locale'],
            'template_engine': template['engine'],
            'render_status': 'rendered',
            'rendered_at': timestamp()
        }
        
        updated_message = await self.stm.update(message, **updates)
        
        logger.info(f"Server-rendered message {message['_id']} using template {template['key']} v{template['version']}")
        
        return updated_message
    
    async def _prepare_for_client_render(
        self,
        message: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare message for client-side rendering."""
        
        # Store template reference for client
        updates = {
            'template_version': template['version'],
            'template_locale': template['locale'],
            'template_engine': template['engine'],
            'render_status': 'ready_client_render',
            'rendered_at': timestamp()
        }
        
        updated_message = await self.stm.update(message, **updates)
        
        logger.info(f"Prepared message {message['_id']} for client rendering using template {template['key']} v{template['version']}")
        
        return updated_message
    
    async def _mark_processing_failed(self, message: Dict[str, Any], error: str):
        """Mark message processing as failed."""
        updates = {
            'render_status': 'failed',
            'render_error': error,
            'rendered_at': timestamp()
        }
        
        await self.stm.update(message, **updates)
    
    def _get_content_type_for_engine(self, engine: str) -> str:
        """Get appropriate content type for template engine."""
        engine_content_types = {
            'jinja2': 'text/html',
            'markdown': 'text/html',
            'txt': 'text/plain',
            'static': 'text/plain'
        }
        return engine_content_types.get(engine, 'text/plain')
    
    async def retry_failed_processing(self, message_id: str) -> Dict[str, Any]:
        """Retry processing for a failed message."""
        message = await self.stm.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")
        
        if message['render_status'] != 'failed':
            raise ValueError(f"Message {message_id} is not in failed state")
        
        # Reset status and retry
        await self.stm.update(message, render_status='pending', render_error=None)
        return await self.process_message_content(message)