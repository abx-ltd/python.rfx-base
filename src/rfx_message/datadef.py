from typing import Optional, List
from pydantic import Field
from datetime import datetime

from fluvius.data import DataModel, UUID_TYPE

from .types import MessageType, ContentType, PriorityLevel

class SendMessagePayload(DataModel):
    """Payload for creating a new notification
    
    Recipients are typically determined by business logic/domain events,
    not manually specified by users.
    """

    #Reference fields
    thread_id: Optional[UUID_TYPE] = Field(default=None, description="ID of the message thread")

    #Content and Metadata fields
    subject: Optional[str] = Field(default=None, max_length=255, description="Subject of the notification")
    content: str = Field(min_length=10, max_length=1024, description="Content of the notification")
    content_type: Optional[ContentType] = Field(default=ContentType.TEXT, description="Type of content in the notification")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the notification")
    is_important: Optional[bool] = Field(default=False, description="Flag to mark the notification as important")
    expirable: Optional[bool] = Field(default=False, description="Flag to indicate if the notification is expirable")
    message_type: Optional[MessageType] = Field(default=MessageType.NOTIFICATION, description="Type of the notification")
    priority: Optional[PriorityLevel] = Field(default=PriorityLevel.MEDIUM, description="Priority level of the notification")
    expiration_date: Optional[datetime] = Field(default=None, description="Expiration date of the notification")
    data: Optional[dict] = Field(default_factory=dict, description="Additional data associated with the notification")
    context: Optional[dict] = Field(default_factory=dict, description="Contextual information for the notification")
    request_read_receipt: Optional[datetime] = Field(default=None, description="Request for read receipt with timestamp")
    mtype: str = Field(default="notification", description="Type identifier for routing")

    #Recipient fields (typically determined by business logic)
    recipients: Optional[List[UUID_TYPE]] = Field(default_factory=list, description="List of recipient IDs (usually set by domain events)")


class ReadMessagePayload(DataModel):
    """Payload for marking a message as read"""
    
    message_id: UUID_TYPE = Field(description="ID of the message to mark as read")

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