from typing import Optional, List, Dict, Any
from pydantic import Field, model_validator
from enum import Enum
from datetime import datetime

from fluvius.data import DataModel, UUID_TYPE, UUID_GENR
from .types import MessageTypeEnum, PriorityLevelEnum, ContentTypeEnum, RenderStrategyEnum

class SendMessagePayload(DataModel):
    """
    Enhanced payload for sending notification messages.
    Supports both template-based and direct content messages.
    """
    
    # Recipients (required)
    recipients: List[UUID_TYPE] = Field(default_factory=list, description="List of recipient user IDs")

    # Message metadata
    subject: Optional[str] = Field(None, description="Message subject")
    message_type: MessageTypeEnum = Field(MessageTypeEnum.NOTIFICATION, description="Type of message")
    priority: PriorityLevelEnum = Field(PriorityLevelEnum.MEDIUM, description="Message priority")
    
    # Content source (one of these must be provided)
    content: Optional[str] = Field(None, description="Direct message content (no template)")
    content_type: Optional[ContentTypeEnum] = Field(ContentTypeEnum.TEXT, description="Content type")
    
    # Template-based content
    template_key: Optional[str] = Field(None, description="Template key for rendering")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Data for template rendering")
    template_version: Optional[int] = Field(None, description="Specific template version")
    
    # Rendering control
    render_strategy: Optional[str] = Field(None, description="Override rendering strategy")
    
    # Context for template resolution
    template_locale: Optional[str] = Field("en", description="Locale for template resolution")
    template_channel: Optional[str] = Field(None, description="Channel for template resolution")
    tenant_id: Optional[UUID_TYPE] = Field(None, description="Tenant ID for scoped templates")
    app_id: Optional[str] = Field(None, description="App ID for scoped templates")
    
    # Additional metadata
    tags: Optional[List[str]] = Field([], description="Message tags")
    expiration_date: Optional[datetime] = Field(None, description="Message expiration time")
    
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

class CreateTemplatePayload(DataModel):
    """Payload for creating message templates."""
    
    key: str = Field(..., description="Template key identifier")
    name: Optional[str] = Field(None, description="Human-readable template name")
    context: str = Field(..., description="Template body/source code")
    
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
    # sample_data: Optional[Dict[str, Any]] = Field({}, description="Sample data for testing")
    
    # Rendering control
    render_strategy: Optional[RenderStrategyEnum] = Field(None, description="Default rendering strategy")

class PublishTemplatePayload(DataModel):
    """Payload for publishing templates."""
    
    template_id: UUID_TYPE = Field(..., description="Template ID to publish")

# class ProcessContentPayload(DataModel):
#     """Payload for processing message content."""
    
#     message_id: UUID_TYPE = Field(..., description="Message ID to process")
#     mode: str = Field("SYNC", description="Processing mode: SYNC, ASYNC, IMMEDIATE")
#     context: Optional[Dict[str, Any]] = Field({}, description="Additional context for processing")

# DTO for response Message
class Notification(DataModel):
    message_id: UUID_TYPE = Field(..., description="ID of the message")
    recipient_id: Optional[UUID_TYPE] = Field(None, description="ID of the recipient")
    sender_id: Optional[UUID_TYPE] = Field(None, description="ID of the sender")

    subject: str = Field(..., description="Subject of the message")
    content: str = Field(..., description="Content of the message")
    content_type: str = Field(..., description="Content type of the message")
    priority: PriorityLevelEnum = Field(PriorityLevelEnum.MEDIUM, description="Priority level of the message")

    is_important: Optional[bool] = Field(False, description="Whether the message is marked as important")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date of the message")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags associated with the message")

    # Template fields for client rendering
    template_key: Optional[str] = Field(None, description="Template key used for rendering")
    template_version: Optional[int] = Field(None, description="Version of the template used")
    template_locale: Optional[str] = Field("en", description="Locale for the template")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Additional data for the template")
    render_strategy: Optional[RenderStrategyEnum] = Field(None, description="Rendering strategy for the template")

