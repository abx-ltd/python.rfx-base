from typing import Optional, List, Dict, Any
from pydantic import Field, model_validator
from datetime import datetime
from .types import MessageCategoryEnum
from fluvius.data import DataModel, UUID_TYPE


class SendMessagePayload(DataModel):
    """
    Enhanced payload for sending notification messages.
    Supports both template-based and direct content messages.
    """

    # Recipients (required)
    recipients: List[UUID_TYPE] = Field(
        default_factory=list, description="List of recipient user IDs"
    )

    # Message metadata
    subject: Optional[str] = Field(None, description="Message subject")
    message_type: str = Field("NOTIFICATION", description="Type of message")
    priority: str = Field("MEDIUM", description="Message priority")

    # Content source (one of these must be provided)
    content: Optional[str] = Field(
        None, description="Direct message content (no template)"
    )
    content_type: Optional[str] = Field("TEXT", description="Content type")

    # Template-based content
    template_key: Optional[str] = Field(None, description="Template key for rendering")
    template_data: Optional[Dict[str, Any]] = Field(
        None, description="Data for template rendering"
    )
    template_version: Optional[int] = Field(
        None, description="Specific template version"
    )

    # Rendering control
    render_strategy: Optional[str] = Field(
        None, description="Override rendering strategy"
    )

    # Context for template resolution
    template_locale: Optional[str] = Field(
        "en", description="Locale for template resolution"
    )
    template_channel: Optional[str] = Field(
        None, description="Channel for template resolution"
    )
    tenant_id: Optional[UUID_TYPE] = Field(
        None, description="Tenant ID for scoped templates"
    )
    app_id: Optional[str] = Field(None, description="App ID for scoped templates")

    # Additional metadata
    tags: Optional[List[str]] = Field([], description="Message tags")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Additional data for the message"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Message expiration time"
    )
    category: Optional[MessageCategoryEnum] = Field(
        None, description="Message category"
    )

    @model_validator(mode="after")
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


class ReplyMessagePayload(DataModel):
    """
    Enhanced payload for sending notification messages.
    Supports both template-based and direct content messages.
    """

    # Message metadata
    message_type: str = Field("NOTIFICATION", description="Type of message")
    priority: str = Field("MEDIUM", description="Message priority")

    # Content source (one of these must be provided)
    content: Optional[str] = Field(
        None, description="Direct message content (no template)"
    )
    content_type: Optional[str] = Field("TEXT", description="Content type")

    # Template-based content
    template_key: Optional[str] = Field(None, description="Template key for rendering")
    template_data: Optional[Dict[str, Any]] = Field(
        None, description="Data for template rendering"
    )
    template_version: Optional[int] = Field(
        None, description="Specific template version"
    )

    # Rendering control
    render_strategy: Optional[str] = Field(
        None, description="Override rendering strategy"
    )

    # Context for template resolution
    template_locale: Optional[str] = Field(
        "en", description="Locale for template resolution"
    )
    template_channel: Optional[str] = Field(
        None, description="Channel for template resolution"
    )
    tenant_id: Optional[UUID_TYPE] = Field(
        None, description="Tenant ID for scoped templates"
    )
    app_id: Optional[str] = Field(None, description="App ID for scoped templates")

    # Additional metadata
    tags: Optional[List[str]] = Field([], description="Message tags")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Additional data for the message"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Message expiration time"
    )
    category: Optional[MessageCategoryEnum] = Field(
        None, description="Message category"
    )

    @model_validator(mode="after")
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


class SetMessageCategoryPayload(DataModel):
    """Payload for setting the category of a message."""

    recipient_id: UUID_TYPE = Field(None, description="Recipient ID")
    category: MessageCategoryEnum = Field(
        default=MessageCategoryEnum.INFORMATION, description="Message category"
    )


class CreateTemplatePayload(DataModel):
    """Payload for creating message templates."""

    key: str = Field(..., description="Template key identifier")
    name: Optional[str] = Field(None, description="Human-readable template name")
    context: str = Field(..., description="Template body/source code")

    # Template configuration
    engine: str = Field("jinja2", description="Template engine")
    locale: str = Field("en", description="Template locale")
    channel: Optional[str] = Field(None, description="Template channel")
    version: Optional[int] = Field(None, description="Template version number")

    # Multi-tenant scoping
    tenant_id: Optional[UUID_TYPE] = Field(None, description="Tenant ID")
    app_id: Optional[str] = Field(None, description="App ID")

    # Template metadata
    description: Optional[str] = Field(None, description="Template description")
    variables_schema: Optional[Dict[str, Any]] = Field(
        {}, description="JSON schema for template variables"
    )
    # sample_data: Optional[Dict[str, Any]] = Field({}, description="Sample data for testing")

    # Rendering control
    render_strategy: Optional[str] = Field(
        None, description="Default rendering strategy"
    )


# class PublishTemplatePayload(DataModel):
#     """Payload for publishing templates."""

#     template_id: UUID_TYPE = Field(..., description="Template ID to publish")

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
    priority: str = Field("MEDIUM", description="Priority level of the message")

    is_important: Optional[bool] = Field(
        False, description="Whether the message is marked as important"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Expiration date of the message"
    )
    tags: Optional[list[str]] = Field(
        default_factory=list, description="Tags associated with the message"
    )
    data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Arbitrary message metadata payload"
    )

    # Template fields for client rendering
    template_key: Optional[str] = Field(
        None, description="Template key used for rendering"
    )
    template_version: Optional[int] = Field(
        None, description="Version of the template used"
    )
    template_locale: Optional[str] = Field("en", description="Locale for the template")
    template_data: Optional[Dict[str, Any]] = Field(
        None, description="Additional data for the template"
    )
    render_strategy: Optional[str] = Field(
        None, description="Rendering strategy for the template"
    )
