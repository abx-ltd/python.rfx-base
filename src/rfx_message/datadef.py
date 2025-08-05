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
