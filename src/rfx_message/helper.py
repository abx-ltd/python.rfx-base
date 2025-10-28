from enum import Enum
from typing import Dict, Optional, Any
from .datadef import Notification

from .types import MessageTypeEnum, RenderStrategyEnum, ProcessingModeEnum, ContentTypeEnum, PriorityLevelEnum



MESSAGE_RENDERING_MAP = {
    MessageTypeEnum.NOTIFICATION: RenderStrategyEnum.CACHED,   # High volume, can use cached templates
    MessageTypeEnum.ALERT: RenderStrategyEnum.SERVER,          # Critical, needs server-side rendering for reliability
    MessageTypeEnum.REMINDER: RenderStrategyEnum.CLIENT,       # Dynamic content, client-side for personalization
    MessageTypeEnum.SYSTEM: RenderStrategyEnum.STATIC,         # Administrative, usually static content
    MessageTypeEnum.USER: RenderStrategyEnum.CLIENT,           # User-generated, interactive content
}

def get_render_strategy(message_type: MessageTypeEnum) -> RenderStrategyEnum:
    """
    Get the appropriate template rendering strategy for a notification type.
    
    Rendering strategies:
    - SERVER: Server-side template rendering for critical/reliable content
    - CLIENT: Client-side template rendering for dynamic/interactive content
    - CACHED: Pre-rendered templates cached for high-volume notifications
    - STATIC: Static templates without dynamic content for simple messages
    """
    return MESSAGE_RENDERING_MAP.get(message_type, RenderStrategyEnum.SERVER)

def render_on_server(strategy: RenderStrategyEnum) -> bool:
    return strategy in (RenderStrategyEnum.SERVER, RenderStrategyEnum.CACHED, RenderStrategyEnum.STATIC)

def render_on_client(strategy: RenderStrategyEnum) -> bool:
    return strategy in (RenderStrategyEnum.CLIENT)

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

async def determine_processing_mode(message_type: MessageTypeEnum, payload: dict) -> ProcessingModeEnum:
    """Determine how to process the message based on type and content."""
    
    # Direct content can be processed immediately
    if payload.get('content'):
        return ProcessingModeEnum.SYNC
    
    # Critical alerts are always immediate
    if message_type == MessageTypeEnum.ALERT:
        return ProcessingModeEnum.IMMEDIATE
    
    # High priority messages
    if payload.get('priority') == 'high':
        return ProcessingModeEnum.SYNC
    
    # Template-based messages with client rendering can be fast
    strategy = payload.get('render_strategy')
    if strategy == RenderStrategyEnum.CLIENT.value:
        return ProcessingModeEnum.SYNC
    
    # Default to async for complex rendering
    return ProcessingModeEnum.ASYNC

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
        content_type=getattr(message, "content_type", ContentTypeEnum.TEXT),
        priority=getattr(message, "priority", PriorityLevelEnum.MEDIUM),
        is_important=getattr(message, "is_important", False) or False,
        expiration_date=getattr(message, "expiration_date", None),
        tags=getattr(message, "tags", []) or [],
        
        # Template information for client rendering
        template_key=getattr(message, "template_key", None),
        template_version=getattr(message, "template_version", None),
        template_locale=getattr(message, "template_locale", None),
        template_data=getattr(message, "template_data", {}) or {},
        render_strategy=getattr(message, "render_strategy", RenderStrategyEnum.SERVER),
    )
