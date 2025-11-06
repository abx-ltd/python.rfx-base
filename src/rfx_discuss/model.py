import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import config


class RFXDiscussConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_discuss.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXDiscussBaseModel(RFXDiscussConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": config.RFX_DISCUSS_SCHEMA}

    _realm = sa.Column(sa.String)


# ================ Comment Context ================


class Comment(RFXDiscussBaseModel):
    __tablename__ = "comment"

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)


class CommentView(RFXDiscussBaseModel):
    __tablename__ = "_comment"
    __table_args__ = {"schema": config.RFX_DISCUSS_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)
    attachment_count = sa.Column(sa.Integer)
    reaction_count = sa.Column(sa.Integer)
    flag_count = sa.Column(sa.Integer)


class CommentAttachment(RFXDiscussBaseModel):
    __tablename__ = "comment_attachment"

    comment_id = sa.Column(pg.UUID, nullable=False)
    file_url = sa.Column(sa.String(1024), nullable=False)
    file_name = sa.Column(sa.String(255), nullable=False)
    file_type = sa.Column(sa.String(100))
    file_size = sa.Column(sa.Integer)
    file_extension = sa.Column(sa.String(20))

    # Image-specific fields
    is_image = sa.Column(sa.Boolean, default=False)
    image_width = sa.Column(sa.Integer)
    image_height = sa.Column(sa.Integer)
    thumbnail_url = sa.Column(sa.String(1024))
    # Upload status
    upload_status = sa.Column(sa.String(20), default="completed")


class CommentAttachmentView(RFXDiscussBaseModel):
    __tablename__ = "_comment_attachment"

    comment_id = sa.Column(pg.UUID)
    file_url = sa.Column(sa.String(1024))
    file_name = sa.Column(sa.String(255))
    file_type = sa.Column(sa.String(100))
    file_size = sa.Column(sa.Integer)
    file_extension = sa.Column(sa.String(20))
    is_image = sa.Column(sa.Boolean)
    image_width = sa.Column(sa.Integer)
    image_height = sa.Column(sa.Integer)
    thumbnail_url = sa.Column(sa.String(1024))
    upload_status = sa.Column(sa.String(20))
    uploader = sa.Column(pg.JSONB)


class CommentReaction(RFXDiscussBaseModel):
    __tablename__ = "comment_reaction"

    comment_id = sa.Column(pg.UUID, nullable=False)
    user_id = sa.Column(pg.UUID, nullable=False)
    reaction_type = sa.Column(sa.String(50), nullable=False)


class CommentReactionView(RFXDiscussBaseModel):
    __tablename__ = "_comment_reaction"

    comment_id = sa.Column(pg.UUID)
    user_id = sa.Column(pg.UUID)
    reaction_type = sa.Column(sa.String(50))
    reactor = sa.Column(pg.JSONB)


class CommentReactionSummary(RFXDiscussBaseModel):
    """Aggregated reaction counts per comment and type"""

    __tablename__ = "_comment_reaction_summary"
    __table_args__ = {"schema": config.RFX_DISCUSS_SCHEMA}

    comment_id = sa.Column(pg.UUID)
    reaction_type = sa.Column(sa.String(50))
    reaction_count = sa.Column(sa.Integer)
    users = sa.Column(pg.JSONB)


class CommentFlag(RFXDiscussBaseModel):
    __tablename__ = "comment_flag"

    comment_id = sa.Column(pg.UUID, nullable=False)
    reported_by_user_id = sa.Column(pg.UUID, nullable=False)
    reason = sa.Column(sa.String(100), nullable=False)
    status = sa.Column(sa.String(50), default="pending", nullable=False)
    description = sa.Column(sa.Text)


class CommentFlagView(RFXDiscussBaseModel):
    __tablename__ = "_comment_flag"

    comment_id = sa.Column(pg.UUID)
    reported_by_user_id = sa.Column(pg.UUID)
    reason = sa.Column(sa.String(100))
    status = sa.Column(sa.String(50))
    description = sa.Column(sa.Text)
    reporter = sa.Column(pg.JSONB)
    comment_preview = sa.Column(pg.JSONB)


class CommentFlagResolution(RFXDiscussBaseModel):
    __tablename__ = "comment_flag_resolution"

    flag_id = sa.Column(pg.UUID, nullable=False, unique=True)
    resolved_by_user_id = sa.Column(pg.UUID, nullable=False)
    resolved_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    resolution_note = sa.Column(sa.Text)
    resolution_action = sa.Column(sa.String(50))


class CommentFlagResolutionView(RFXDiscussBaseModel):
    __tablename__ = "_comment_flag_resolution"

    flag_id = sa.Column(pg.UUID)
    resolved_by_user_id = sa.Column(pg.UUID)
    resolved_at = sa.Column(sa.DateTime(timezone=True))
    resolution_note = sa.Column(sa.Text)
    resolution_action = sa.Column(sa.String(50))
    resolver = sa.Column(pg.JSONB)
    flag_info = sa.Column(pg.JSONB)
    comment_id = sa.Column(pg.UUID)


class CommentFlagSummary(RFXDiscussBaseModel):
    __tablename__ = "_comment_flag_summary"

    comment_id = sa.Column(pg.UUID, primary_key=True)
    total_flags = sa.Column(sa.Integer)
    pending_flags = sa.Column(sa.Integer)
    resolved_flags = sa.Column(sa.Integer)
    rejected_flags = sa.Column(sa.Integer)
    flag_reasons = sa.Column(pg.JSONB)  # [{reason: count}]
    latest_flag_at = sa.Column(sa.DateTime(timezone=True))
