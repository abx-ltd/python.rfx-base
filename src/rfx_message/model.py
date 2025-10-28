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
from datetime import datetime
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

# class ViewBaseModel(MessageConnector.__data_schema_base__):
#     """Base model class for views in the message service."""
#     __abstract__ = True
#     __table_args__ = {'schema': config.MESSAGE_SERVICE_SCHEMA}


class Message(MServiceBaseModel):
    """
    Core message entity containing content, metadata, and relationships.
    Supports rich content, priority levels, expiration, and thread organization.
    """

    __tablename__ = "message"

    # Reference fields
    sender_id = sa.Column(pg.UUID)
    thread_id = sa.Column(pg.UUID)

    # Message Content fields
    subject = sa.Column(sa.String(1024))
    content = sa.Column(sa.String(1024))
    rendered_content = sa.Column(sa.String(1024))
    content_type = sa.Column(
        sa.Enum(types.ContentTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
    )

    # Message Metadata fields
    tags = sa.Column(pg.ARRAY(sa.String))
    is_important = sa.Column(sa.Boolean, default=False)
    expirable = sa.Column(sa.Boolean, default=False)
    expiration_date = sa.Column(sa.DateTime(timezone=True))
    request_read_receipt = sa.Column(sa.DateTime(timezone=True))
    priority = sa.Column(
        sa.Enum(types.PriorityLevelEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        default=types.PriorityLevelEnum.MEDIUM,
        nullable=False
    )
    message_type = sa.Column(
        sa.Enum(types.MessageTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
    )
    delivery_status = sa.Column(
        sa.Enum(types.DeliveryStatusEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        default=types.DeliveryStatusEnum.PENDING,
        nullable=False
    )

    # Additional metadata fields
    data = sa.Column(pg.JSONB, default=dict)
    context = sa.Column(pg.JSONB, default=dict)
    mtype = sa.Column(sa.String(255), nullable=False)

    # Template rendering fields
    template_key = sa.Column(sa.String(255))
    template_version = sa.Column(sa.Integer)
    template_locale = sa.Column(sa.String(10))
    template_engine = sa.Column(sa.String(32))
    template_data = sa.Column(pg.JSONB, default=dict)

    # Rendering Control and Status
    render_strategy = sa.Column(
        sa.Enum(types.RenderStrategyEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        nullable=True
    )
    render_status = sa.Column(
        sa.Enum(types.RenderStatusEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        nullable=True
    )
    rendered_at = sa.Column(sa.DateTime(timezone=True),
                            default=datetime.utcnow)
    render_error = sa.Column(sa.Text)


class MessageAction(MServiceBaseModel):
    """
    Defines actionable buttons/links within messages (e.g., approve, reject, view).
    Supports HTTP calls with authentication and different targets.
    """

    __tablename__ = "message_action"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))

    # Content fields
    type = sa.Column(sa.Enum(types.ActionTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA))
    name = sa.Column(sa.String(1024))
    description = sa.Column(sa.String(1024))

    # Action metadata fields
    authentication = sa.Column(pg.JSONB, default=dict)
    payload = sa.Column(pg.JSONB, default=dict)
    host = sa.Column(sa.String(1024))
    endpoint = sa.Column(sa.String())
    method = sa.Column(sa.Enum(
        types.HTTPMethodEnum, schema=config.MESSAGE_SERVICE_SCHEMA))
    is_primary = sa.Column(sa.Boolean, default=False)
    mobile_endpoint = sa.Column(sa.String(1024))
    destination = sa.Column(pg.ARRAY(sa.String), default=list)
    target = sa.Column(sa.Enum(
        types.HTTPTargetEnum, schema=config.MESSAGE_SERVICE_SCHEMA))


class MessageBox(MServiceBaseModel):
    """
    Message containers/folders for organizing messages (inbox, sent, custom folders).
    Supports email aliases and different box types.
    """

    __tablename__ = "message_box"

    _txt = sa.Column(pg.TSVECTOR)  # Full-text search vector
    name = sa.Column(sa.String(1024))
    email_alias = sa.Column(sa.Text())
    type = sa.Column(sa.Enum(types.BoxTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA))


class MessageBoxUser(MServiceBaseModel):
    """
    Junction table linking users to message boxes for access control.
    """

    __tablename__ = "message_box_user"

    # Reference fields
    user_id = sa.Column(pg.UUID)
    box_id = sa.Column(pg.UUID, sa.ForeignKey(MessageBox._id))


class MessageRecipient(MServiceBaseModel):
    """
    Tracks message delivery and recipient-specific metadata.
    Manages read status, archiving, labels, and message direction.
    """

    __tablename__ = "message_recipient"

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
        sa.Enum(types.MessageTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
    )


class MessageRecipientAction(MServiceBaseModel):
    """
    Tracks when recipients execute message actions and stores responses.
    """

    __tablename__ = "message_recipient_action"

    # Reference fields
    message_recipient_id = sa.Column(
        pg.UUID, sa.ForeignKey(MessageRecipient._id))
    action_id = sa.Column(pg.UUID, sa.ForeignKey(MessageAction._id))

    # Action metadata fields
    response = sa.Column(pg.JSONB, default=dict)


class MessageAttachment(MServiceBaseModel):
    """
    Links file attachments to messages.
    """

    __tablename__ = "message_attachment"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(
        Message._id), primary_key=True)
    file_id = sa.Column(pg.UUID)


class MessageEmbedded(MServiceBaseModel):
    """
    Embedded content within messages (widgets, external content, previews).
    Supports various embed types with configurable options.
    """

    __tablename__ = "message_embedded"

    # Reference fields
    _iid = sa.Column(pg.UUID)
    message_id = sa.Column(pg.UUID, sa.ForeignKey(Message._id))

    # Content fields
    type = sa.Column(sa.String(255))
    title = sa.Column(sa.String(255))
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

    __tablename__ = "message_reference"

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

    name = sa.Column(sa.String(255), primary_key=True,
                     nullable=False, unique=True)
    background_color = sa.Column(sa.String(7))  # Hex color code
    font_color = sa.Column(sa.String(7))  # Hex color code
    description = sa.Column(sa.String(1024))
    group = sa.Column(sa.Enum(types.TagGroupEnum, schema=config.MESSAGE_SERVICE_SCHEMA))


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

    __tablename__ = "tag_preference"

    option = sa.Column(pg.JSONB, default=dict)


class RefRole(MServiceBaseModel):
    """
    Reference table for role definitions used in the message system.
    """

    __tablename__ = "ref__role"

    key = sa.Column(sa.String(255), primary_key=True,
                    nullable=False, unique=True)


class MessageTemplate(MServiceBaseModel):
    """
    Template for creating new messages.
    """
    __tablename__ = "message_template"

    # Template fields
    key = sa.Column(sa.String(255), nullable=False)
    version = sa.Column(sa.Integer, default=1)
    locale = sa.Column(sa.String(10), default="en")  # optional
    # e.g., "inapp", "email", "sms" (optional)
    channel = sa.Column(sa.String(32))

    # TODO: Multitenant
    tenant_id = sa.Column(pg.UUID)
    app_id = sa.Column(sa.String(64))

    # Content and engine
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    engine = sa.Column(sa.String(32), default='jinja2')
    context = sa.Column(pg.TEXT)

    # Variables schema
    variables_schema = sa.Column(pg.JSONB, default=dict)
    # sample_data = sa.Column(pg.JSONB, default=dict)  # Sample data for rendering

    # Rendering control
    render_strategy = sa.Column(
        sa.Enum(types.RenderStrategyEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        nullable=True
    )  # Override default strategy for this template

    # Meta
    status = sa.Column(
        sa.Enum(types.TemplateStatusEnum, schema=config.MESSAGE_SERVICE_SCHEMA),
        default=types.TemplateStatusEnum.DRAFT.value
    )
    is_active = sa.Column(sa.Boolean, default=True)

    __table_args__ = (
        # Ensure unique templates per scope
        sa.UniqueConstraint('tenant_id', 'app_id', 'key', 'version',
                            'locale', 'channel', name='uq_template_scope'),
        {'schema': config.MESSAGE_SERVICE_SCHEMA}  # Ensure schema is set
    )


class TemplateRenderCache(MServiceBaseModel):
    """
    Caches the rendered output of message templates.
    """
    __tablename__ = "template_render_cache"

    # Cache key components
    template_key = sa.Column(sa.String(255), nullable=False)
    template_version = sa.Column(sa.Integer, default=1)
    locale = sa.Column(sa.String(10), default="en")
    channel = sa.Column(sa.String(32))  # e.g., "inapp",

    # Cache content
    compiled_template = sa.Column(sa.LargeBinary)
    last_accessed = sa.Column(pg.TIMESTAMP, default=datetime.utcnow)
    access_count = sa.Column(sa.Integer, default=0)

    # TTL and invalidation
    expires_at = sa.Column(pg.TIMESTAMP)
    is_valid = sa.Column(sa.Boolean, default=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "template_key", "template_version", "locale", "channel", name="uq_cache_key"
        ),
        {'schema': config.MESSAGE_SERVICE_SCHEMA}
    )


class MessageRecipientsView(MServiceBaseModel):
    """
    Database view that joins message and message-recipient tables.
    Provides a flattened view for notification queries with recipient-specific data.
    """
    __tablename__ = "_message_recipients"

    # Primary composite key
    record_id = sa.Column(pg.UUID, primary_key=True)
    recipient_id = sa.Column(pg.UUID)

    # Message content fields
    subject = sa.Column(sa.String(1024))
    content = sa.Column(sa.String(1024))
    content_type = sa.Column(
        sa.Enum(types.ContentTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA)
    )

    # Message metadata fields
    sender_id = sa.Column(pg.UUID)
    tags = sa.Column(pg.ARRAY(sa.String))
    expirable = sa.Column(sa.Boolean)
    priority = sa.Column(
        sa.Enum(types.PriorityLevelEnum, schema=config.MESSAGE_SERVICE_SCHEMA)
    )
    message_type = sa.Column(
        sa.Enum(types.MessageTypeEnum, schema=config.MESSAGE_SERVICE_SCHEMA)
    )

    # Recipient-specific fields
    is_read = sa.Column(sa.Boolean, default=False)
    read_at = sa.Column(sa.DateTime(timezone=True))
    archived = sa.Column(sa.Boolean, default=False)
