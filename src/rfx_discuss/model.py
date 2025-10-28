import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import config


class RFXDiscussConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_discuss.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXDiscussBaseModel(RFXDiscussConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": config.RFX_DISCUSSION_SCHEMA}

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
    __table_args__ = {"schema": config.RFX_DISCUSSION_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)
