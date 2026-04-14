import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import config, logger


class RFXDiscussConnector(SqlaDriver):
    __db_dsn__ = config.DB_DSN

