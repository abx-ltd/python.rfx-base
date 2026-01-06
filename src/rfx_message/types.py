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


class DirectionTypeEnum(Enum):
    """
    Message direction classifications for routing and processing.
    Determines the flow of messages within the system.
    """

    INCOMING = "INCOMING"  # Message received from external source
    OUTGOING = "OUTGOING"  # Message sent to external recipient
    SYSTEM = "SYSTEM"  # System-generated message, not user-initiated


class ActionTypeEnum(Enum):
    """
    Action type classifications for message processing actions.
    Determines the type of action taken on a message.
    """

    HTTP = "HTTP"  # HTTP request action
    LINK = "LINK"  # Link action, typically for external resources


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


class TagGroupEnum(Enum):
    """
    Tag groups for organizing and categorizing tags.
    """

    APPLICATION = "APPLICATION"  # Tags related to application functionality
    FUNCTION = "FUNCTION"  # Tags related to specific functions or features


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


class MessageCategoryEnum(Enum):
    """
    Message category classifications for message organization and filtering.
    """

    IMPORTANT = "IMPORTANT"  # Important messages requiring attention
    URGENT = "URGENT"  # Urgent messages requiring immediate action
    INFORMATION = "INFORMATION"  # Informational messages for reference
