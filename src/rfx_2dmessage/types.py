"""
RFX Message Domain Type Definitions

Enum definitions for message content types and status values used throughout
the messaging system for content classification and delivery management.
"""

from enum import Enum


class ContentTypeEnum(Enum):
    """
    Message content type classifications for proper rendering and processing.
    Determines how message content should be interpreted and displayed.
    """

    TEXT = "TEXT"  # Plain text content
    HTML = "HTML"  # HTML formatted content
    MARKDOWN = "MARKDOWN"  # Markdown formatted content
    JSON = "JSON"  # Structured JSON data
    XML = "XML"  # XML formatted content


class PriorityLevelEnum(Enum):
    """
    Message priority levels for delivery and processing urgency.
    Determines how messages are prioritized in the system.
    """

    LOW = "LOW"  # Low priority, can be processed later
    MEDIUM = "MEDIUM"  # Normal priority, standard processing
    HIGH = "HIGH"  # High priority, urgent processing required


class MessageTypeEnum(Enum):
    """
    Message type classifications for routing and handling.
    Determines how messages are categorized within the system.
    """

    NOTIFICATION = "NOTIFICATION"  # General notification message
    ALERT = "ALERT"  # Urgent alert message
    REMINDER = "REMINDER"  # Reminder message
    SYSTEM = "SYSTEM"  # System-generated message
    USER = "USER"  # User-generated message


class DeliveryStatusEnum(Enum):
    """
    Message delivery status classifications for tracking message delivery progress.
    """

    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class DirectionTypeEnum(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class ActionTypeEnum(Enum):
    """
    Action type classifications for message processing actions.
    Determines the type of action taken on a message.
    """

    ATOMIC = "ATOMIC"  # No data collection needed, single confirmation
    FORM = "FORM"  # User fills form before submission
    EMBEDDED = "EMBEDDED"  # Remote server renders UI in modal/frame


class ExecutionModeEnum(Enum):
    """
    Execution mode for actions - how the action is performed.
    """

    API = "API"  # Direct API call to configured endpoint
    EMBED = "EMBED"  # Load remote URL with callback handling


class ActionExecutionStatus(Enum):
    """
    Status of action execution.
    """

    PENDING = "PENDING"  # Execution started but not completed
    COMPLETED = "COMPLETED"  # Execution finished successfully
    FAILED = "FAILED"  # Execution failed
    CANCELLED = "CANCELLED"  # Execution was cancelled


class HTTPMethodEnum(Enum):
    """
    HTTP methods used for message actions.
    Determines the type of HTTP request made.
    """

    GET = "GET"  # Retrieve resource
    POST = "POST"  # Create resource
    DELETE = "DELETE"  # Delete resource
    PATCH = "PATCH"  # Partially update resource


class HTTPTargetEnum(Enum):
    """
    HTTP target classifications for message actions.
    Determines the target of the HTTP request.
    """

    BLANK = "BLANK"  # Open in new tab/window
    IFRAME = "IFRAME"  # Open in an iframe


class BoxTypeEnum(Enum):
    """
    Message box types for categorizing message boxes.
    """

    GROUP = "GROUP"  # Group message box, shared among users
    SINGLE = "SINGLE"  # Single user message box, personal to the user


class RenderStatusEnum(Enum):
    """
    Rendering status for message content.
    """

    PENDING = "PENDING"  # Rendering is pending
    IN_PROGRESS = "IN_PROGRESS"  # Rendering is in progress
    COMPLETED = "COMPLETED"  # Rendering is completed
    CLIENT_RENDERING = "CLIENT_RENDERING"  # Rendering from client
    FAILED = "FAILED"  # Rendering has failed


class TemplateStatusEnum(Enum):
    """
    Template rendering status for message content.
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class RenderStrategyEnum(Enum):
    SERVER = "SERVER"  # Server-side template rendering
    CLIENT = "CLIENT"  # Client-side template rendering
    CACHED = "CACHED"  # Pre-rendered templates stored in cache
    STATIC = "STATIC"  # Static templates without dynamic content


# Processing Mode, Don't have in DB
class ProcessingModeEnum(Enum):
    SYNC = "SYNC"  # Process immediately (blocking)
    ASYNC = "ASYNC"  # Process in background
    IMMEDIATE = "IMMEDIATE"  # For critical alerts


class MessageCategoryEnum(str, Enum):
    """
    Message category classifications for message organization and filtering.
    """

    IMPORTANT = "IMPORTANT"  # Important messages requiring attention
    URGENT = "URGENT"  # Urgent messages requiring immediate action
    INFORMATION = "INFORMATION"  # Informational messages for reference

class MailBoxTypeEnum(str, Enum):
    """
    Mailbox type classifications for categorizing message mailboxes.
    """

    EMAIL = "EMAIL"
    SMS = "SMS"
    NOTIFICATION = "NOTIFICATION"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    SYSTEM = "SYSTEM"
    WEBHOOK = "WEBHOOK"

class MailBoxMessageStatusTypeEnum(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    DONE = "DONE"
    
class MailBoxMemberRoleEnum(str, Enum):
    OWNER = "OWNER"
    CONTRIBUTOR = "CONTRIBUTOR"
    VIEWER = "VIEWER"


class MediaTypeEnum(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    ARCHIVE = "ARCHIVE"
    OTHER = "OTHER"