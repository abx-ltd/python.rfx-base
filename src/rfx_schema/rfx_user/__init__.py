from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fluvius.data import DomainSchema, SqlaDriver
from rfx_user import config as domain_config

# --- Connector and Base Schema ---
class RFXUserConnector(SqlaDriver):
    __db_dsn__ = domain_config.DB_DSN
    __schema__ = domain_config.USER_PROFILE_SCHEMA


class Base(RFXUserConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": domain_config.USER_PROFILE_SCHEMA}


class PolicyBase(RFXUserConnector.__data_schema_base__):
    __abstract__ = True
    __table_args__ = {
        "schema": domain_config.USER_PROFILE_SCHEMA,
        "info": {"is_view": True},
    }


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = domain_config.USER_PROFILE_SCHEMA
from rfx_schema.rfx_policy import SCHEMA as POLICY_SCHEMA



from . import _schema
from . import _viewmap
