import sqlalchemy as sa

from fluvius.data import SqlaDriver, UUID_GENR
from sqlalchemy.dialects import postgresql as pg


from . import config


class RFXCqrsDomainSchema:
    _id = sa.Column(pg.UUID, primary_key=True, nullable=False,
                    default=UUID_GENR, server_default=sa.text("uuid_generate_v4()"))
    _created = sa.Column(sa.DateTime(timezone=True),
                         nullable=False, server_default=sa.text("now()"))
    _creator = sa.Column(pg.UUID, default=UUID_GENR)


class RFXCqrsConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_cqrs.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXCqrsBaseModel(RFXCqrsConnector.__data_schema_base__, RFXCqrsDomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.RFX_CQRS_SCHEMA}


class ActivityLog(RFXCqrsBaseModel):
    __tablename__ = "activity-log"

    domain = sa.Column(sa.String(255), nullable=False)
    identifier = sa.Column(pg.UUID, nullable=False)
    resource = sa.Column(sa.String(255), nullable=False)
    message = sa.Column(sa.String(255), nullable=False)
    msgtype = sa.Column(sa.String(255), nullable=False)
    msglabel = sa.Column(sa.String(255), nullable=False)
    context = sa.Column(pg.UUID, nullable=False)
    src_cmd = sa.Column(pg.UUID, nullable=False)
    src_evt = sa.Column(pg.UUID, nullable=False)
    data = sa.Column(sa.JSON, nullable=False)
    code = sa.Column(sa.Integer, nullable=False)
