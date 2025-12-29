from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR

from . import config as qr_config
from . import types


class QRConnector(SqlaDriver):
    """Database connector for the QR code service."""
    assert qr_config.DB_DSN, "[rfx_qr.DB_DSN] not set."

    __db_dsn__ = qr_config.DB_DSN
