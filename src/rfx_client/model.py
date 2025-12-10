import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg

from . import types, config


class RFXClientConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN
