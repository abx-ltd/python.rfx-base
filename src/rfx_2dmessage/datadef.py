# Data definitions for command payloads
# Define Pydantic models for command data here

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, model_validator


from fluvius.data import DataModel, UUID_TYPE
from .types import MessageCategoryEnum


# class CreateMessagePayload(BaseModel):
#     ...

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

    # # Template-based content
    # template_key: Optional[str] = Field(None, description="Template key for rendering")
    # template_data: Optional[Dict[str, Any]] = Field(
    #     None, description="Data for template rendering"
    # )
    # template_version: Optional[int] = Field(
    #     None, description="Specific template version"
    # )

    # # Rendering control
    # render_strategy: Optional[str] = Field(
    #     None, description="Override rendering strategy"
    # )

    # # Context for template resolution
    # template_locale: Optional[str] = Field(
    #     "en", description="Locale for template resolution"
    # )
    # template_channel: Optional[str] = Field(
    #     None, description="Channel for template resolution"
    # )
    # tenant_id: Optional[UUID_TYPE] = Field(
    #     None, description="Tenant ID for scoped templates"
    # )
    # app_id: Optional[str] = Field(None, description="App ID for scoped templates")

    # # Additional metadata
    # tags: Optional[List[str]] = Field([], description="Message tags")
    # data: Optional[Dict[str, Any]] = Field(
    #     None, description="Additional data for the message"
    # )
    # expiration_date: Optional[datetime] = Field(
    #     None, description="Message expiration time"
    # )
    # category: Optional[MessageCategoryEnum] = Field(
    #     None, description="Message category"
    # )