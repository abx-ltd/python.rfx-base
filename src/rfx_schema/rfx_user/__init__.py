from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fluvius.data import DomainSchema, SqlaDriver
from rfx_schema._meta import config as schema_config

# --- Connector and Base Schema ---
class RFXUserConnector(SqlaDriver):
    __db_dsn__ = schema_config.RFX_USER_DB_DSN
    __schema__ = schema_config.RFX_USER_SCHEMA


class Base(RFXUserConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": schema_config.RFX_USER_SCHEMA}


class PolicyBase(RFXUserConnector.__data_schema_base__):
    __abstract__ = True
    __table_args__ = {
        "schema": schema_config.RFX_USER_SCHEMA,
        "info": {"is_view": True},
    }


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = schema_config.RFX_USER_SCHEMA
POLICY_SCHEMA = schema_config.RFX_POLICY_SCHEMA



from . import _schema
from . import _viewmap
