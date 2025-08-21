import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import types, config


class RFXDiscussionConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_discussion.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXDiscussionBaseModel(RFXDiscussionConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    _realm = sa.Column(sa.String)

# ================ Ticket Context ================
# Ticket Aggregate Root


class Ticket(RFXDiscussionBaseModel):
    __tablename__ = "ticket"

    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.RFX_DISCUSSION_SCHEMA),
        nullable=False
    )
    type = sa.Column(sa.String(100), nullable=False)  # FK to ref--ticket-type
    parent_id = sa.Column(pg.UUID)  # FK to ticket(_id)
    assignee = sa.Column(pg.UUID)  # FK to profile(_id)
    status = sa.Column(sa.String(100), nullable=False)  # FK to ticket_status
    workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)
    availability = sa.Column(
        sa.Enum(types.Availability, name="availability",
                schema=config.RFX_DISCUSSION_SCHEMA),
        nullable=False
    )
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.RFX_DISCUSSION_SCHEMA),
        default=types.SyncStatus.PENDING
    )
    is_inquiry = sa.Column(sa.Boolean, default=True)
    organization_id = sa.Column(pg.UUID)


# Ticket Status Entity
class TicketStatus(RFXDiscussionBaseModel):
    __tablename__ = "ticket-status"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


# Ticket Comment Entity
class TicketComment(RFXDiscussionBaseModel):
    __tablename__ = "ticket-comment"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    comment_id = sa.Column(pg.UUID, nullable=False)  # FK to comment(_id)


# Ticket Assignee Entity
class TicketAssignee(RFXDiscussionBaseModel):
    __tablename__ = "ticket-assignee"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)


# Ticket Participants Entity
class TicketParticipants(RFXDiscussionBaseModel):
    __tablename__ = "ticket-participant"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    participant_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)


# Ticket Tag Entity
class TicketTag(RFXDiscussionBaseModel):
    __tablename__ = "ticket-tag"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    tag_id = sa.Column(pg.UUID, nullable=False)  # FK to tag(_id)


class RefTicketType(RFXDiscussionBaseModel):
    __tablename__ = "ref--ticket-type"

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    icon_color = sa.Column(sa.String(7))  # Hex color code
    is_active = sa.Column(sa.Boolean, default=True)
    is_inquiry = sa.Column(sa.Boolean, default=True)


# View for inquiry listing
class ViewInquiry(RFXDiscussionBaseModel):
    __tablename__ = "_inquiry"
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    type = sa.Column(sa.String(255), primary_key=True)
    type_icon_color = sa.Column(sa.String(7))  # Hex color code
    title = sa.Column(sa.String(255), nullable=False)
    tag_names = sa.Column(pg.ARRAY(sa.String))
    participants = sa.Column(pg.JSONB)
    availability = sa.Column(
        sa.Enum(types.Availability, name="availability",
                schema=config.RFX_DISCUSSION_SCHEMA),
        nullable=False
    )
    organization_id = sa.Column(pg.UUID)


class ViewTicket(RFXDiscussionBaseModel):
    __tablename__ = "_ticket"
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(sa.String(100), nullable=False)
    type = sa.Column(sa.String(100), nullable=False)
    parent_id = sa.Column(pg.UUID)
    assignee = sa.Column(pg.UUID)
    status = sa.Column(sa.String(100), nullable=False)
    workflow_id = sa.Column(pg.UUID)
    availability = sa.Column(
        sa.Enum(types.Availability, name="availability",
                schema=config.RFX_DISCUSSION_SCHEMA),
        nullable=False
    )
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.RFX_DISCUSSION_SCHEMA),
        default=types.SyncStatus.PENDING
    )
    project_id = sa.Column(pg.UUID)
    organization_id = sa.Column(pg.UUID)


# ================ Tag Context ================s

# Tag Aggregate Root
class Tag(RFXDiscussionBaseModel):
    __tablename__ = "tag"

    key = sa.Column(sa.String(50), nullable=False, unique=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)
    target_resource = sa.Column(sa.String(100), nullable=False)
    organization_id = sa.Column(pg.UUID)

# ================ Comment Context ================


class Comment(RFXDiscussionBaseModel):
    __tablename__ = "comment"

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    organization_id = sa.Column(pg.UUID)


class CommentView(RFXDiscussionBaseModel):
    __tablename__ = "_comment"
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    ticket_id = sa.Column(pg.UUID)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)
