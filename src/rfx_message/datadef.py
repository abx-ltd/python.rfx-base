from typing import Optional, List
from pydantic import Field
from datetime import datetime

from fluvius.data import DataModel, UUID_TYPE

from .types import MessageType, ContentType, PriorityLevel

class SendMessagePayload(DataModel):
    """Payload for creating a new message"""

    #Reference fields
    # sender_id: UUID_TYPE = Field(default=None, description="ID of the sender")
    thread_id: Optional[UUID_TYPE] = Field(default=None, description="ID of the message thread")

    #Content and Metadata fields
    subject: Optional[str] = Field(default=None, max_length=255, description="Subject of the message")
    content: str = Field(min_length=10, max_length=1024, description="Content of the message")
    content_type: Optional[ContentType] = Field(default=ContentType.TEXT, description="Type of content in the message")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the message")
    is_important: Optional[bool] = Field(default=False, description="Flag to mark the message as important")
    expirable: Optional[bool] = Field(default=False, description="Flag to indicate if the message is expirable")
    message_type: Optional[MessageType] = Field(default=MessageType.NOTIFICATION, description="Type of the message")
    priority: Optional[PriorityLevel] = Field(default=PriorityLevel.MEDIUM, description="Priority level of the message")
    is_important: Optional[bool] = Field(default=False, description="Flag to mark the message as important")
    expiration_date: Optional[datetime] = Field(default=None, description="Expiration date of the message")
    data: Optional[dict] = Field(default_factory=dict, description="Additional data associated with the message")
    context: Optional[dict] = Field(default_factory=dict, description="Contextual information for the message")
    request_read_receipt: Optional[datetime] = Field(default=None, description="Request for read receipt with timestamp")
    mtype: str = Field(default="message", description="Type of the message, used for routing or processing")
    # sender_id: Optional[UUID_TYPE] = Field(default=None, description="ID of the sender")

    #Recipient fields
    recipients: Optional[List[UUID_TYPE]] = Field(default_factory=list, description="List of recipient IDs")


class ReadMessagePayload(DataModel):
    """Payload for marking a message as read"""
    
    message_id: UUID_TYPE = Field(description="ID of the message to mark as read")


class UpdateMessagePayload(DataModel):
    """Payload for updating an existing message"""
    
    message_id: UUID_TYPE = Field(description="ID of the message to update")
    subject: Optional[str] = Field(default=None, max_length=255, description="Updated subject")
    content: Optional[str] = Field(default=None, max_length=1024, description="Updated content")
    content_type: Optional[ContentType] = Field(default=None, description="Updated content type")
    tags: Optional[List[str]] = Field(default=None, description="Updated tags")
    is_important: Optional[bool] = Field(default=None, description="Updated importance flag")
    priority: Optional[PriorityLevel] = Field(default=None, description="Updated priority")
    expiration_date: Optional[datetime] = Field(default=None, description="Updated expiration date")


class DeleteMessagePayload(DataModel):
    """Payload for deleting a message"""
    
    message_id: UUID_TYPE = Field(description="ID of the message to delete")


class AddRecipientsPayload(DataModel):
    """Payload for adding recipients to a message"""
    
    message_id: UUID_TYPE = Field(description="ID of the message")
    recipients: List[UUID_TYPE] = Field(min_items=1, description="List of recipient IDs to add")


class RemoveRecipientPayload(DataModel):
    """Payload for removing a recipient from a message"""
    
    message_id: UUID_TYPE = Field(description="ID of the message")
    recipient_id: UUID_TYPE = Field(description="ID of the recipient to remove")


class AddAttachmentPayload(DataModel):
    """Payload for adding an attachment to a message"""
    
    message_id: UUID_TYPE = Field(description="ID of the message")
    file_name: str = Field(max_length=255, description="Name of the attachment file")
    file_url: str = Field(description="URL or path to the attachment file")
    file_size: Optional[int] = Field(default=None, description="Size of the file in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type of the file")
    description: Optional[str] = Field(default=None, max_length=500, description="Description of the attachment")


class NotificationMessageData(DataModel):
    """Data model for notification message dispatch (for background processing)"""
    
    message_id: UUID_TYPE = Field(description="ID of the message")
    sender_id: UUID_TYPE = Field(description="ID of the sender")
    recipients: List[UUID_TYPE] = Field(description="List of recipient IDs")
    
    # Message content for notification
    subject: Optional[str] = Field(default=None, description="Message subject")
    content: str = Field(description="Message content")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Content type")
    tags: List[str] = Field(default_factory=list, description="Message tags")
    is_important: bool = Field(default=False, description="Importance flag")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Priority level")
    expirable: bool = Field(default=False, description="Expirable flag")
    expiration_date: Optional[datetime] = Field(default=None, description="Expiration date")
    thread_id: Optional[UUID_TYPE] = Field(default=None, description="Thread ID")
    mtype: str = Field(default="message", description="Message type")
    
    # Dispatch configuration
    command: str = Field(default="send-notification", description="Command to execute")