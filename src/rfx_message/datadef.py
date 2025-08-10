from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from enum import Enum

from fluvius.data import UUID_TYPE
from .types import MessageType, PriorityLevel, ContentType
from .helper import RenderingStrategy

class SendMessagePayload(BaseModel):
    """
    Enhanced payload for sending notification messages.
    Supports both template-based and direct content messages.
    """
    
    # Recipients (required)
    recipients: List[UUID_TYPE] = Field(..., description="List of recipient user IDs")
    
    # Message metadata
    subject: Optional[str] = Field(None, description="Message subject")
    message_type: MessageType = Field(MessageType.NOTIFICATION, description="Type of message")
    priority: PriorityLevel = Field(PriorityLevel.MEDIUM, description="Message priority")
    
    # Content source (one of these must be provided)
    content: Optional[str] = Field(None, description="Direct message content (no template)")
    content_type: Optional[ContentType] = Field(ContentType.TEXT, description="Content type")
    
    # Template-based content
    template_key: Optional[str] = Field(None, description="Template key for rendering")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Data for template rendering")
    template_version: Optional[int] = Field(None, description="Specific template version")
    
    # Rendering control
    render_strategy: Optional[RenderingStrategy] = Field(None, description="Override rendering strategy")
    
    # Context for template resolution
    locale: Optional[str] = Field("en", description="Locale for template resolution")
    channel: Optional[str] = Field(None, description="Channel for template resolution")
    tenant_id: Optional[UUID_TYPE] = Field(None, description="Tenant ID for scoped templates")
    app_id: Optional[str] = Field(None, description="App ID for scoped templates")
    
    # Additional metadata
    tags: Optional[List[str]] = Field([], description="Message tags")
    expires_at: Optional[str] = Field(None, description="Message expiration time")
    
    @model_validator(mode='after')
    def validate_content_source(self):
        """Ensure either content or template_key is provided."""
        if not self.content and not self.template_key:
            raise ValueError("Either 'content' or 'template_key' must be provided")
        
        if self.content and self.template_key:
            raise ValueError("Cannot provide both 'content' and 'template_key'")
        
        if self.template_key and not self.template_data:
            # Allow empty template_data but warn
            self.template_data = {}
        
        return self

class CreateTemplatePayload(BaseModel):
    """Payload for creating message templates."""
    
    key: str = Field(..., description="Template key identifier")
    name: Optional[str] = Field(None, description="Human-readable template name")
    body: str = Field(..., description="Template body/source code")
    
    # Template configuration
    engine: str = Field("jinja2", description="Template engine")
    locale: str = Field("en", description="Template locale")
    channel: Optional[str] = Field(None, description="Template channel")
    
    # Multi-tenant scoping
    tenant_id: Optional[UUID_TYPE] = Field(None, description="Tenant ID")
    app_id: Optional[str] = Field(None, description="App ID")
    
    # Template metadata
    description: Optional[str] = Field(None, description="Template description")
    variables_schema: Optional[Dict[str, Any]] = Field({}, description="JSON schema for template variables")
    sample_data: Optional[Dict[str, Any]] = Field({}, description="Sample data for testing")
    
    # Rendering control
    render_strategy: Optional[RenderingStrategy] = Field(None, description="Default rendering strategy")

class PublishTemplatePayload(BaseModel):
    """Payload for publishing templates."""
    
    template_id: UUID_TYPE = Field(..., description="Template ID to publish")

class ProcessContentPayload(BaseModel):
    """Payload for processing message content."""
    
    message_id: UUID_TYPE = Field(..., description="Message ID to process")
    mode: str = Field("sync", description="Processing mode: sync, async, immediate")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context for processing")