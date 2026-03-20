from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fluvius.data import DomainSchema, SqlaDriver
from rfx_media import config as domain_config

# --- Connector and Base Schema ---
class RFXMediaConnector(SqlaDriver):
    __db_dsn__ = domain_config.DB_DSN
    __schema__ = domain_config.RFX_MEDIA_SCHEMA


class Base(RFXMediaConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": domain_config.RFX_MEDIA_SCHEMA}


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = domain_config.RFX_MEDIA_SCHEMA



# Ensure ORM schemas and view maps register when module loads.
from . import _schema  # noqa: F401
from . import _viewmap  # noqa: F401
