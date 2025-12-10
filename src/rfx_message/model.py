from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR

from . import config, types


class MessageConnector(SqlaDriver):
    """Database connector for the message service."""
    assert config.DB_DSN, "[rfx_message.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN
