from enum import Enum
from typing import Dict, Optional, Any
from .datadef import Notification

from .types import MessageType, RenderStrategy, ProcessingMode, ContentType, PriorityLevel



MESSAGE_RENDERING_MAP = {
    MessageType.NOTIFICATION: RenderStrategy.CACHED,   # High volume, can use cached templates
    MessageType.ALERT: RenderStrategy.SERVER,          # Critical, needs server-side rendering for reliability
    MessageType.REMINDER: RenderStrategy.CLIENT,       # Dynamic content, client-side for personalization
    MessageType.SYSTEM: RenderStrategy.STATIC,         # Administrative, usually static content
    MessageType.USER: RenderStrategy.CLIENT,           # User-generated, interactive content
}

def get_render_strategy(message_type: MessageType) -> RenderStrategy:
    """
    Get the appropriate template rendering strategy for a notification type.
    
    Rendering strategies:
    - SERVER: Server-side template rendering for critical/reliable content
    - CLIENT: Client-side template rendering for dynamic/interactive content
    - CACHED: Pre-rendered templates cached for high-volume notifications
    - STATIC: Static templates without dynamic content for simple messages
    """
    return MESSAGE_RENDERING_MAP.get(message_type, RenderStrategy.SERVER)

def render_on_server(strategy: RenderStrategy) -> bool:
    return strategy in (RenderStrategy.SERVER, RenderStrategy.CACHED, RenderStrategy.STATIC)

def render_on_client(strategy: RenderStrategy) -> bool:
    return strategy in (RenderStrategy.CLIENT)

def extract_template_context(payload: Dict[str, Any], *, default_locale: str = "en") -> Dict[str, Any]:
    """
    Extract template context from the payload.
    """
    return {
        "tenant_id": payload.get("tenant_id"),
        "app_id": payload.get("app_id"),
        "locale": payload.get("locale", default_locale),
        "channel": payload.get("channel"),
    }

async def determine_processing_mode(message_type: MessageType, payload: dict) -> ProcessingMode:
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
    if strategy == RenderStrategy.CLIENT.value:
        return ProcessingMode.SYNC
    
    # Default to async for complex rendering
    return ProcessingMode.ASYNC

def message_to_notification_data(message):
    """
    Convert a Message model to a Notification data structure for client consumption.
    
    Args:
        message: Message DataModel instance
        recipient_id: ID of the specific recipient
    
    Returns:
        Notification DataModel instance
    """
    
    return Notification(
        message_id=getattr(message, "_id", None),
        sender_id=getattr(message, "sender_id", None),
        subject=getattr(message, "subject", "") or "",
        content=getattr(message, "rendered_content", None),
        content_type=getattr(message, "content_type", ContentType.TEXT),
        priority=getattr(message, "priority", PriorityLevel.MEDIUM),
        is_important=getattr(message, "is_important", False) or False,
        expiration_date=getattr(message, "expiration_date", None),
        tags=getattr(message, "tags", []) or [],
        
        # Template information for client rendering
        template_key=getattr(message, "template_key", None),
        template_version=getattr(message, "template_version", None),
        template_locale=getattr(message, "template_locale", None),
        template_data=getattr(message, "template_data", {}) or {},
        render_strategy=getattr(message, "render_strategy", RenderStrategy.SERVER),
    )
