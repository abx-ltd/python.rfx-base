"""
Message Service Database Models

This module defines SQLAlchemy models for a comprehensive messaging system that supports:
- Rich message content with attachments and embeds
- Message actions and recipient interactions
- Message boxes and user management
- Tagging and labeling system
- Reference management
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR

from . import config, types

class MessageConnector(SqlaDriver):
    """Database connector for the message service."""
    assert config.DB_DSN, "[rfx_message.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN

class MServiceBaseModel(MessageConnector.__data_schema_base__, DomainSchema):
    """Base model class for all message service models."""
    __abstract__ = True
    __table_args__ = {'schema': config.MESSAGE_SERVICE_SCHEMA}

    _realm = sa.Column(sa.String)

class ViewBaseModel(MessageConnector.__data_schema_base__):
    """Base model class for views in the message service."""
    __abstract__ = True
    __table_args__ = {'schema': config.MESSAGE_SERVICE_SCHEMA}

class Message(MServiceBaseModel):
    """
    Core message entity containing content, metadata, and relationships.
    Supports rich content, priority levels, expiration, and thread organization.
    """

    __tablename__ = "message"

    # Message Content fields
    subject = sa.Column(sa.String(1024))
    content = sa.Column(sa.String(1024))

    # Message Metadata fields
    tags = sa.Column(pg.ARRAY(sa.String))
    is_important = sa.Column(sa.Boolean, default=False)
    expirable = sa.Column(sa.Boolean, default=False)
    expiration_date = sa.Column(sa.DateTime(timezone=True))
    request_read_receipt = sa.Column(sa.DateTime(timezone=True))
    priority = sa.Column(
        sa.Enum(types.PriorityLevel, name="priority_level", schema=config.MESSAGE_SERVICE_SCHEMA),
        default=types.PriorityLevel.MEDIUM,
        nullable=False
    )
    message_type = sa.Column(
        sa.Enum(types.MessageType, name="message_type", schema=config.MESSAGE_SERVICE_SCHEMA),
    )
    content_type = sa.Column(
        sa.Enum(types.ContentType, name="content_type", schema=config.MESSAGE_SERVICE_SCHEMA),
    )

    # Reference fields
    sender_id = sa.Column(pg.UUID)
    thread_id = sa.Column(pg.UUID)

    # Additional metadata fields
    data = sa.Column(pg.JSONB, default=dict)
    context = sa.Column(pg.JSONB, default=dict)
    mtype = sa.Column(sa.String(255), nullable=False)

class MessageAction(MServiceBaseModel):
    """
    Defines actionable buttons/links within messages (e.g., approve, reject, view).
    Supports HTTP calls with authentication and different targets.
    """
    
    __tablename__ = "message-action"
    
    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))

    # Content fields
    type = sa.Column(sa.Enum(types.ActionType, name="action_type", schema=config.MESSAGE_SERVICE_SCHEMA))
    name = sa.Column(sa.String(1024))
    description = sa.Column(sa.String(1024))

    # Action metadata fields
    authentication = sa.Column(pg.JSONB, default=dict)
    payload = sa.Column(pg.JSONB, default=dict)
    host = sa.Column(sa.String(1024))
    endpoint = sa.Column(sa.String())
    method = sa.Column(sa.Enum(types.HTTPMETHOD, name="http_method", schema=config.MESSAGE_SERVICE_SCHEMA))
    is_primary = sa.Column(sa.Boolean, default=False) 
    mobile_endpoint = sa.Column(sa.String(1024))
    destination = sa.Column(pg.ARRAY(sa.String), default=list)
    target = sa.Column(sa.Enum(types.HTTPTARGET, name="http_target", schema=config.MESSAGE_SERVICE_SCHEMA))

class MessageBox(MServiceBaseModel):
    """
    Message containers/folders for organizing messages (inbox, sent, custom folders).
    Supports email aliases and different box types.
    """

    __tablename__ = "message-box"

    _txt = sa.Column(pg.TSVECTOR)  # Full-text search vector
    name = sa.Column(sa.String(1024))
    email_alias = sa.Column(sa.Text())
    type = sa.Column(sa.Enum(types.BOXTYPE, name="box_type", schema=config.MESSAGE_SERVICE_SCHEMA))

class MessageBoxUser(MServiceBaseModel):
    """
    Junction table linking users to message boxes for access control.
    """
    
    __tablename__ = "message-box-user"

    # Reference fields
    user_id = sa.Column(pg.UUID)
    box_id = sa.Column(pg.UUID, sa.ForeignKey(MessageBox._id))

class MessageRecipient(MServiceBaseModel):
    """
    Tracks message delivery and recipient-specific metadata.
    Manages read status, archiving, labels, and message direction.
    """
    
    __tablename__ = "message-recipient"

    # Reference fields
    recipient_id = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))
    executed_action_id = sa.Column(pg.UUID, sa.ForeignKey(MessageAction._id))
    last_reply_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))
    box_id = sa.Column(pg.UUID, sa.ForeignKey(MessageBox._id))

    # Recipient metadata fields
    read = sa.Column(sa.Boolean, default=False)
    mark_as_read = sa.Column(sa.DateTime(timezone=True))
    archived = sa.Column(sa.Boolean, default=False)
    is_ignored = sa.Column(sa.DateTime(timezone=True))
    label = sa.Column(sa.ARRAY(pg.UUID), default=list)
    direction = sa.Column(
        sa.Enum(types.MessageType, name="message_direction", schema=config.MESSAGE_SERVICE_SCHEMA),
    )

class MessageRecipientAction(MServiceBaseModel):
    """
    Tracks when recipients execute message actions and stores responses.
    """
    
    __tablename__ = "message-recipient-action"

    # Reference fields
    message_recipient_id = sa.Column(pg.UUID, sa.ForeignKey(MessageRecipient._id))
    action_id = sa.Column(pg.UUID, sa.ForeignKey(MessageAction._id))

    # Action metadata fields
    response = sa.Column(pg.JSONB, default=dict)

class MessageAttachment(MServiceBaseModel):
    """
    Links file attachments to messages.
    """
    
    __tablename__ = "message-attachment"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id), primary_key=True)
    file_id = sa.Column(pg.UUID)

class MessageEmbedded(MServiceBaseModel):
    """
    Embedded content within messages (widgets, external content, previews).
    Supports various embed types with configurable options.
    """
    
    __tablename__ = "message-embedded"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))

    # Content fields
    type = sa.Column(sa.String(255))
    title= sa.Column(sa.String(255))
    description = sa.Column(sa.String(1024))
    host = sa.Column(sa.String(1024))
    endpoint = sa.Column(sa.String(1024))

    # Additional metadata fields
    options = sa.Column(pg.JSONB, default=dict)

class MessageReference(MServiceBaseModel):
    """
    Links messages to external resources (documents, contacts, etc.).
    Supports various reference types with metadata and contact information.
    """
    
    __tablename__ = "message-reference"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))
    resource_id = sa.Column(pg.UUID)

    # Content Fields
    description = sa.Column(sa.String(1024))
    favorited = sa.Column(sa.Boolean, default=False)
    kind = sa.Column(sa.String(1024))
    resource = sa.Column(sa.String(1024))
    source = sa.Column(sa.String(1024))
    url = sa.Column(sa.String(1024))
    title = sa.Column(sa.String(1024))
    telecom__email = sa.Column(sa.String(255))
    telecom__phone = sa.Column(sa.String(12))

class Tag(MServiceBaseModel):
    """
    System-wide tags for categorizing messages.
    Supports visual customization and grouping.
    """
    
    __tablename__ = "tag"

    name = sa.Column(sa.String(255), primary_key=True, nullable=False, unique=True)
    background_color = sa.Column(sa.String(7))  # Hex color code
    font_color = sa.Column(sa.String(7))  # Hex color code
    description = sa.Column(sa.String(1024))
    group = sa.Column(sa.Enum(types.TAGGROUP, name="tag_group", schema=config.MESSAGE_SERVICE_SCHEMA))
    
class Label(MServiceBaseModel):
    """
    User-specific labels for personal message organization.
    Supports visual customization per user.
    """
    
    __tablename__ = "label"

    # Reference fields
    user_id = sa.Column(pg.UUID)
    name = sa.Column(sa.String(255), nullable=False, unique=True)
    background_color = sa.Column(sa.String(7))  # Hex color code
    font_color = sa.Column(sa.String(7))  # Hex color code

class TagPreference(MServiceBaseModel):
    """
    User preferences for tag behavior and display options.
    """
    
    __tablename__ = "tag-preference"

    option = sa.Column(pg.JSONB, default=dict)

class RefRole(MServiceBaseModel):
    """
    Reference table for role definitions used in the message system.
    """
    
    __tablename__ = "ref--role"

    key = sa.Column(sa.String(255), primary_key=True, nullable=False, unique=True)

class MessageRecipientsView(ViewBaseModel):
    """
    Database view that joins message and message-recipient tables.
    Provides a flattened view for notification queries with recipient-specific data.
    """
    __tablename__ = "_message_recipients"

    # Primary composite key
    record_id = sa.Column(pg.UUID, primary_key=True)
    message_id = sa.Column(pg.UUID)
    recipient_id = sa.Column(pg.UUID)

    # Message content fields
    subject = sa.Column(sa.String(1024))
    content = sa.Column(sa.String(1024))
    content_type = sa.Column(
        sa.Enum(types.ContentType, name="content_type", schema=config.MESSAGE_SERVICE_SCHEMA)
    )
    
    # Message metadata fields  
    sender_id = sa.Column(pg.UUID)
    tags = sa.Column(pg.ARRAY(sa.String))
    expirable = sa.Column(sa.Boolean)
    priority = sa.Column(
        sa.Enum(types.PriorityLevel, name="priority_level", schema=config.MESSAGE_SERVICE_SCHEMA)
    )
    message_type = sa.Column(
        sa.Enum(types.MessageType, name="message_type", schema=config.MESSAGE_SERVICE_SCHEMA)
    )
    
    # Recipient-specific fields
    is_read = sa.Column(sa.Boolean, default=False)
    read_at = sa.Column(sa.DateTime(timezone=True)) 
    archived = sa.Column(sa.Boolean, default=False)