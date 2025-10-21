import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import types, config


class RFXDiscussConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_discussion.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXDiscussBaseModel(RFXDiscussConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    _realm = sa.Column(sa.String)

# ================ Comment Context ================


class Comment(RFXDiscussBaseModel):
    __tablename__ = "comment"

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    organization_id = sa.Column(pg.UUID)


class CommentView(RFXDiscussBaseModel):
    __tablename__ = "_comment"
    __table_args__ = {'schema': config.RFX_DISCUSSION_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    ticket_id = sa.Column(pg.UUID)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)

# ================ Workflow Context ================


class Status(RFXDiscussBaseModel):
    __tablename__ = "status"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    entity_type = sa.Column(sa.String(100), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)


class StatusKey(RFXDiscussBaseModel):
    __tablename__ = "status-key"

    status_id = sa.Column(sa.ForeignKey(Status._id), nullable=False)
    key = sa.Column(sa.String(100), nullable=False, unique=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_initial = sa.Column(sa.Boolean, default=False)
    is_final = sa.Column(sa.Boolean, default=False)


class StatusTransition(RFXDiscussBaseModel):
    __tablename__ = "status-transition"

    status_id = sa.Column(sa.ForeignKey(Status._id), nullable=False)
    src_status_key_id = sa.Column(sa.ForeignKey(
        StatusKey._id), nullable=False)
    dst_status_key_id = sa.Column(sa.ForeignKey(
        StatusKey._id), nullable=False)


class ViewStatus(RFXDiscussBaseModel):
    __tablename__ = "_status"

    entity_type = sa.Column(sa.String(100), nullable=False)
    status_id = sa.Column(pg.UUID, primary_key=True)
    key = sa.Column(sa.String(100), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_initial = sa.Column(sa.Boolean, nullable=False)
    is_final = sa.Column(sa.Boolean, nullable=False)
  
#======= Comment Integration Context =======
class CommentIntegration(RFXDiscussBaseModel):
    __tablename__ = "comment-integration"
    __ts_index__ = ["provider", "external_id", "external_url"]
    
    comment_id = sa.Column(sa.ForeignKey(Comment._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)  # e.g., 'linear'
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(255), nullable=False)