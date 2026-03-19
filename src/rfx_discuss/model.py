import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import config


class RFXDiscussConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_discuss.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN

