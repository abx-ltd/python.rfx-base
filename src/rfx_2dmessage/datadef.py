# Data definitions for command payloads
# Define Pydantic models for command data here

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, model_validator


from fluvius.data import DataModel, UUID_TYPE
from .types import(MessageCategoryEnum, 
                   DirectionTypeEnum, 
                   MailBoxMessageStatusTypeEnum, 
                   ActionTypeEnum, 
                   ExecutionModeEnum, 
                   DisplayModeEnum, 
                   CallbackModeEnnum,
                   MessageLinkTypeEnum
)
# class CreateMessagePayload(BaseModel):
#     ...

class SendMessageToMailboxPayload(DataModel):
    """
    Payload for sending notification messages.
    Supports both template-based and direct content messages.
    """

    # Recipients (required)
    mailbox_id: UUID_TYPE = Field(..., description="ID of the target mailbox to send the message to")
    send_all: Optional[bool] = Field(True, description="Whether to send to all members of the mailbox (if True, recipient_ids will be ignored)")
    
    recipients: Optional[List[UUID_TYPE]] = Field(
        default_factory=list, description="List of recipient user IDs"
    )

    # Message metadata
    subject: Optional[str] = Field(None, description="Message subject")
    
    # Content source (one of these must be provided)
    content: Optional[str] = Field(
        None, description="Direct message content (no template)"
    )
    content_type: Optional[str] = Field("TEXT", description="Content type")

    message_type: str = Field("NOTIFICATION", description="Type of message")
    priority: str = Field("MEDIUM", description="Message priority")

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

    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox the tag belongs to")
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
    tag_ids: List[UUID_TYPE] = Field(..., description="IDs of the tags")


class RemoveMessageTagPayload(DataModel):
    """Payload for removing a tag from a message."""
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
    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox the category belongs to")

class UpdateCategoryPayload(DataModel):
    key: Optional[str] = Field(None, description="Key of category")
    name: Optional[str] = Field(..., description="Name of the category" )

# =====================================
# MAILBOX PAYLOAD
# =====================================

class CreateMailboxPayload(DataModel):
    """Payload for creating a new mailbox"""
    name: str = Field(..., description="Display name of the mailbox")
    telecom_phone: Optional[str] = Field(None, description="Phone number for SMS mailbox")
    telecom_email: Optional[str] = Field(None, description="Email address for mailbox")
    description: Optional[str] = Field(None, description="Optional description")
    resource: Optional[str] = Field(None, description="External resource source key")
    url: Optional[str] = Field(None, description="Callback or service URL")
    mailbox_type: Optional[str] = Field(None, description="Type of mailbox (EMAIL,SMS,NOTIFICATION etc)")

    profile_ids: Optional[List[UUID_TYPE]] = Field(None, description="Profile IDs to share the mailbox with. The creator will always have access regardless of this field.")

class UpdateMailboxPayload(DataModel):
    """Payload for update mailbox"""
    name: Optional[str] = Field(None, description="Display name of the mailbox")
    telecom_phone: Optional[str] = Field(None, description="Phone number for SMS mailbox")
    telecom_email: Optional[str] = Field(None, description="Email address for mailbox")
    description: Optional[str] = Field(None, description="Optional description")
    resource: Optional[str] = Field(None, description="External resource source key")
    url: Optional[str] = Field(None, description="Callback or service URL")
    mailbox_type: Optional[str] = Field(None, description="Type of mailbox (EMAIL,SMS,NOTIFICATION etc)")

class AddMemberToMailboxPayload(DataModel):
    """Payload for adding a member to a mailbox"""
    profile_added_ids: List[UUID_TYPE] = Field(None, description="Profile IDs of the members to add")

class AddMessageCategoryPayload(DataModel):
    """Payload for add messages to a category"""
    message_ids: List[UUID_TYPE] = Field(..., description="IDs of the messages")
    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox the category belongs to")

class RemoveMessageCategoryPayload(DataModel):
    """Payload for remove a message from a category"""
    message_ids: List[UUID_TYPE] = Field(..., description="IDs of the messages")
    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox the category belongs to")


class AssignMessagePayload(DataModel):
    """Payload for assigning a message within a mailbox."""

    mailbox_id: UUID_TYPE = Field(..., description="Mailbox ID in which the message is assigned")
    assignee_profile_id: UUID_TYPE = Field(..., description="Profile ID of the assignee")


class SetMessageStatusPayload(DataModel):
    """Payload for updating canonical message status."""

    mailbox_id: UUID_TYPE = Field(..., description="Mailbox ID in which the message is assigned")
    message_status: str = Field(default=MailBoxMessageStatusTypeEnum.NEW, description="Canonical status to set on the message")
    # note: Optional[str] = Field(None, description="Optional note explaining the status change")


class MoveMessagePayload(DataModel):
    """Payload for moving a message inside a mailbox."""

    mailbox_id: UUID_TYPE = Field(..., description="Mailbox ID for the target mailbox view")
    folder: str = Field(default="inbox", description="Folder to move the message into, e.g. inbox or starred")


class SetMessageStarPayload(DataModel):
    """Payload for toggling a mailbox-specific star state."""

    mailbox_id: UUID_TYPE = Field(..., description="Mailbox ID for the target mailbox view")
    starred: bool = Field(default=False, description="True to star the message, False to unstar")


class SetPriorityPayload(DataModel):
    """Payload for updating a message priority."""

    priority: str = Field(..., description="Priority to set on the message, e.g. high, medium, low")


class LinkRelatedMessagePayload(DataModel):
    """Payload for linking related messages."""

    related_message_id: UUID_TYPE = Field(..., description="ID of the related message")
    link_type: Optional[str] = Field("related", description="Type of relation between messages")


class UploadAttachmentMetadataPayload(DataModel):
    """Payload for registering uploaded attachment metadata."""

    storage_key: str = Field(..., description="Storage key for the uploaded attachment")
    filename: str = Field(..., description="Original filename of the uploaded attachment")
    media_type: Optional[str] = Field(None, description="Media type or MIME type of the attachment")
    size_bytes: Optional[int] = Field(None, description="Attachment file size in bytes")
    checksum: Optional[str] = Field(None, description="Optional checksum for the uploaded attachment")


# =====================================
# ACTION PAYLOADS
# =====================================

class CreateActionExecutionPayload(DataModel):
    """Payload for creating an action execution record."""

    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox of the action")
    action_id: UUID_TYPE = Field(..., description="ID of the action to execute")
    # No additional data needed for embedded actions - just starts pending execution

class EndpointConfigPayload(DataModel):
    """Payload for configuring an API endpoint for an action."""

    url: str = Field(..., description="URL of the API endpoint")
    method: str = Field("POST", description="HTTP method to use for the API call")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers to include in the API call")
    timeout_seconds: Optional[int] = Field(30, description="Timeout in seconds for the API call")

class FieldFormConfigPayload(DataModel):
    """Payload for configuring a single field in a form schema."""

    name: str = Field(..., description="Name of the field")
    key: str = Field(..., description="Key of the field for form data mapping")
    type: str = Field(..., description="Data type of the field (e.g. string, number, boolean)")
    label: Optional[str] = Field(None, description="Display label for the field")
    required: bool = Field(False, description="Whether the field is required")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of options for select fields")

class FieldResponseConfigPayload(DataModel):
    """Payload for configuring a single field in the response data mapping."""
    
    key: str = Field(..., description="Key of the field for response data mapping")
    type: str = Field(..., description="Data type of the field (e.g. string, number, boolean)")
    label: Optional[str] = Field(None, description="Display label for the field")

class SchemaConfigPayload(DataModel):
    """Payload for configuring a schema for form actions."""

    fields: List[FieldFormConfigPayload] = Field(..., description="List of field definitions for the form schema")

class ResponseConfigPayload(DataModel):
    """Payload for configuring response handling for an action."""

    success_message: Optional[str] = Field(None, description="Message to return on successful execution")
    error_message: Optional[str] = Field(None, description="Message to return on failed execution")
    response_fields: List[FieldResponseConfigPayload] = Field(None, description="Configuration for fields to include in the response data mapping")

class CallbackConfigPayload(DataModel):
    mode: CallbackModeEnnum = Field(CallbackModeEnnum.POSTMESSAGE, description="Mode of callback from embedded content: POSTMESSAGE, DEEPLINK, or WEBHOOK")
    mechanism: Optional[Dict[str, Any]] = Field(None, description="Configuration for the callback mechanism, e.g. expected message origin for POSTMESSAGE, or callback URL for WEBHOOK")

class DisplayConfigPayload(DataModel):
    """Payload for configuring display for action embedded mode."""
    
    title: Optional[str] = Field(None, description="Title to display for the embedded content")
    mode: DisplayModeEnum = Field(DisplayModeEnum.MODAL, description="Display mode for the embedded content")
    description: Optional[str] = Field(None, description="Description to display for the embedded content")
    width: Optional[int] = Field(600, description="Width of the embedded frame in pixels")
    height: Optional[int] = Field(400, description="Height of the embedded frame in pixels")


class EmbeddedConfigPayload(DataModel):
    """Payload for configuring embedded actions."""

    url: str = Field(..., description="URL to load for the embedded action")
    callback_method: CallbackConfigPayload = Field(None, description="HTTP method to use for the callback from the embedded content")
    display: DisplayConfigPayload = Field(None, description="Display configuration for the embedded content")


class RegisterActionPayload(DataModel):
    """Payload for registering or updating an action definition."""

    action_key: str = Field(..., description="Unique key for the action within the mailbox")
    name: str = Field(..., description="Display name for the action")
    description: Optional[str] = Field(None, description="Optional description of the action")

    execution_mode: ExecutionModeEnum = Field(
        default=ExecutionModeEnum.API, 
        description="Execution mode for the action: API or EMBED"
    )

    action_type: Optional[ActionTypeEnum] = Field(
        default=ActionTypeEnum.ATOMIC, 
        description="Type of action: atomic, form, or embedded")

    authorization_json: Optional[Dict[str, Any]] = Field(None, description="Optional JSON schema for action authorization parameters")

    # Schema for form actions, require if action_type is FORM and execution_mode is API
    schema: Optional[SchemaConfigPayload] = Field(None, description="Schema definition for form actions")

    # Endpoint configuration, require if action_type is ATOMIC or FORM and execution_mode is API
    endpoint: Optional[EndpointConfigPayload] = Field(None, description="Configuration for API endpoint, depending on execution mode")

    # Embedded configuration, require if action_type is EMBEDDED and execution_mode is EMBED
    embedded: EmbeddedConfigPayload = Field(None, description="Configuration for embedded actions, such as URL, dimensions, and callback handling")

    # Response configuration
    response: ResponseConfigPayload = Field(None, description="Response configuration with success/error messages and fields")

class ExecuteAtomicActionPayload(DataModel):
    """Payload for executing an atomic action."""

    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox of the action")
    action_id: UUID_TYPE = Field(..., description="ID of the action to execute")
    # No additional data needed for atomic actions - just confirmation

class SubmitFormActionPayload(DataModel):
    """Payload for submitting a form action."""

    action_id: UUID_TYPE = Field(..., description="ID of the action to execute")
    form_data: Dict[str, Any] = Field(..., description="Form data submitted by the user")

class RecordEmbeddedActionResultPayload(DataModel):
    """Payload for recording the result of an embedded action."""

    action_id: UUID_TYPE = Field(..., description="ID of the action that was executed")
    execution_id: UUID_TYPE = Field(..., description="ID of the action execution")
    callback_payload: Dict[str, Any] = Field(..., description="Callback payload from the embedded action (postMessage, deepLink, or webhook)")


class ActionResponseEnvelope(DataModel):
    """Standard response envelope for action executions."""

    status: str = Field(..., description="Status: success or error")
    action_id: str = Field(..., description="ID of the action that was executed")
    record_id: Optional[str] = Field(None, description="ID of the created record (null on error)")
    timestamp: str = Field(..., description="Timestamp of the response")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data (null on error)")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details (null on success)")


class EmbeddedActionHandoffPayload(DataModel):
    """Response payload for starting an embedded action execution."""

    execution_id: UUID_TYPE = Field(..., description="ID of the created action execution")
    embedded_url: str = Field(..., description="URL to load for the embedded action")
    display: DisplayConfigPayload = Field(..., description="Display configuration for the embedded content")
    callback: CallbackConfigPayload = Field(..., description="Callback configuration for the embedded content")


# =====================================
# LINK MESSAGE PAYLOADS
# =====================================

class LinkMessagePayload(DataModel):
    mailbox_id: UUID_TYPE = Field(..., description="ID of the mailbox of the action")
    left_message_id: UUID_TYPE = Field(..., description="ID of the message link")
    link_type: str = Field(default=MessageLinkTypeEnum.RELATED, description="Message link type")