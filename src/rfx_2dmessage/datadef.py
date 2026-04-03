# Data definitions for command payloads
# Define Pydantic models for command data here

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, model_validator


from fluvius.data import DataModel, UUID_TYPE
from .types import MessageCategoryEnum, DirectionTypeEnum


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

class RemoveMessagePayload(DataModel):
    """Payload for remove a message"""
    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to remove: INBOUND (inbox) or OUTBOUND (outbox). If None, remove both if user sent to themselves.",
    )

class UpdateMessagePayload(DataModel):
    """Payload for update a message"""
    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to archive: INBOUND (inbox) or OUTBOUND (outbox). If None, archive both if user sent to themselves.",
    )

    is_archived: Optional[bool] = Field(None, description="Update is archived True or False")
    is_starred: Optional[bool] = Field(None, description="Update is starred True or False")

class CreateTagPayload(DataModel):
    """Payload for creating a new tag."""

    key: str = Field(..., description="Key of the tag")
    name: str = Field(..., description="Name of the tag")
    background_color: Optional[str] = Field(
        None, description="Background color of the tag"
    )
    font_color: Optional[str] = Field(None, description="Font color of the tag")
    description: Optional[str] = Field(None, description="Description of the tag")


class UpdateTagPayload(DataModel):
    """Payload for updating a tag."""

    key: str = Field(..., description="Key of the tag")
    name: Optional[str] = Field(None, description="Name of the tag")
    background_color: Optional[str] = Field(
        None, description="Background color of the tag"
    )
    font_color: Optional[str] = Field(None, description="Font color of the tag")
    description: Optional[str] = Field(None, description="Description of the tag")


class AddMessageTagPayload(DataModel):
    """Payload for adding a tag to a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to add tag: INBOUND (inbox) or OUTBOUND (outbox). If None, add tag for both if user sent to themselves.",
    )
    tag_ids: List[UUID_TYPE] = Field(..., description="IDs of the tags")


class RemoveMessageTagPayload(DataModel):
    """Payload for removing a tag from a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to remove tag: INBOUND (inbox) or OUTBOUND (outbox). If None, remove tag for both if user sent to themselves.",
    )
    tag_ids: List[UUID_TYPE] = Field(..., description="IDs of the tags")


class UpdateAllMessageTagsPayload(DataModel):
    """Payload for updating all tags for a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to update tags: INBOUND (inbox) or OUTBOUND (outbox). If None, update tags for both if user sent to themselves.",
    )
    tag_ids: List[UUID_TYPE] = Field(..., description="IDs of the tags")

class CreateCategoryPayload(DataModel):
    """Payload for create a new category"""
    key: Optional[str] = Field(None, description="Key of category")
    name: str = Field(..., description="Name of the category" )


class CreateMailboxPayload(DataModel):
    """Payload for creating a new mailbox"""
    name: str = Field(..., description="Display name of the mailbox")
    channel: Optional[str] = Field(..., description="Channel identifier (email/webhook/etc)")
    telecom_phone: Optional[str] = Field(None, description="Phone number for SMS mailbox")
    telecom_email: Optional[str] = Field(None, description="Email address for mailbox")
    description: Optional[str] = Field(None, description="Optional description")
    resource: Optional[str] = Field(None, description="External resource source key")
    url: Optional[str] = Field(None, description="Callback or service URL")
    mailbox_type: Optional[str] = Field(None, description="Type of mailbox (EMAIL,SMS,NOTIFICATION etc)")


class UpdateMailboxPayload(DataModel):
    """Payload for update mailbox"""
    name: Optional[str] = Field(None, description="Display name of the mailbox")
    channel: Optional[str] = Field(None, description="Channel identifier (email/webhook/etc)")
    telecom_phone: Optional[str] = Field(None, description="Phone number for SMS mailbox")
    telecom_email: Optional[str] = Field(None, description="Email address for mailbox")
    description: Optional[str] = Field(None, description="Optional description")
    resource: Optional[str] = Field(None, description="External resource source key")
    url: Optional[str] = Field(None, description="Callback or service URL")
    mailbox_type: Optional[str] = Field(None, description="Type of mailbox (EMAIL,SMS,NOTIFICATION etc)")


class CreateMailboxMessagePayload(DataModel):
    """Payload for adding a mailbox message"""
    message_id: UUID_TYPE = Field(..., description="Message id from canonical message table")
    source: Optional[str] = Field(None, description="Source channel alias")
    source_id: Optional[str] = Field(None, description="External message id")
    category_id: Optional[UUID_TYPE] = Field(None, description="Associated category")
    direction: Optional[str] = Field("INBOUND", description="INBOUND or OUTBOUND")
    status: Optional[str] = Field("NEW", description="Message status")


class AddMessageCategoryPayload(DataModel):
    """Payload for add messages to a category"""
    message_id: List[UUID_TYPE] = Field(..., description="IDs of the messages")
    # direction: Optional[DirectionTypeEnum] = Field(
    #     default=DirectionTypeEnum.INBOUND,
    #     description="Direction to remove: INBOUND (inbox) or OUTBOUND (outbox). If None, remove both if user sent to themselves.",
    # )

class RemoveMessageCategoryPayload(DataModel):
    """Payload for remove a message from a category"""
    message_id: List[UUID_TYPE] = Field(..., description="IDs of the messages")
