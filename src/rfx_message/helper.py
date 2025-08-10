from enum import Enum
from typing import Dict, Optional, Any

from .types import MessageType

class RenderingStrategy(Enum):
    SERVER = "SERVER"        # Server-side template rendering
    CLIENT = "CLIENT"        # Client-side template rendering
    CACHED = "CACHED"        # Pre-rendered templates stored in cache
    STATIC = "STATIC"        # Static templates without dynamic content

MESSAGE_RENDERING_MAP = {
    MessageType.NOTIFICATION: RenderingStrategy.CACHED,   # High volume, can use cached templates
    MessageType.ALERT: RenderingStrategy.SERVER,          # Critical, needs server-side rendering for reliability
    MessageType.REMINDER: RenderingStrategy.CLIENT,       # Dynamic content, client-side for personalization
    MessageType.SYSTEM: RenderingStrategy.STATIC,         # Administrative, usually static content
    MessageType.USER: RenderingStrategy.CLIENT,           # User-generated, interactive content
}

def get_rendering_strategy(message_type: MessageType) -> RenderingStrategy:
    """
    Get the appropriate template rendering strategy for a notification type.
    
    Rendering strategies:
    - SERVER: Server-side template rendering for critical/reliable content
    - CLIENT: Client-side template rendering for dynamic/interactive content
    - CACHED: Pre-rendered templates cached for high-volume notifications
    - STATIC: Static templates without dynamic content for simple messages
    """
    return MESSAGE_RENDERING_MAP.get(message_type, RenderingStrategy.SERVER)

def render_on_server(strategy: RenderingStrategy) -> bool:
    return strategy in (RenderingStrategy.SERVER, RenderingStrategy.CACHED, RenderingStrategy.STATIC)

def render_on_client(strategy: RenderingStrategy) -> bool:
    return strategy in (RenderingStrategy.CLIENT)

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
