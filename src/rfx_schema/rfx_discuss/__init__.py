from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fluvius.data import DomainSchema, SqlaDriver
from rfx_schema._meta import config as schema_config

# --- Connector and Base Schema ---
class RFXDiscussConnector(SqlaDriver):
    __db_dsn__ = schema_config.RFX_DISCUSS_DB_DSN
    __schema__ = schema_config.RFX_DISCUSS_SCHEMA


class Base(RFXDiscussConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": schema_config.RFX_DISCUSS_SCHEMA}


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = schema_config.RFX_DISCUSS_SCHEMA



# Ensure ORM schemas and view maps register when module loads.
from . import _schema  # noqa: F401
from . import _viewmap  # noqa: F401
