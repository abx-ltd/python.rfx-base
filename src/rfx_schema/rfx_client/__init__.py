from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from rfx_base import config
from fluvius.data import DomainSchema, SqlaDriver

from .._meta import config as schema_config

# --- Connector and Base Schema ---
class RFXConnector(SqlaDriver):
    __db_dsn__ = schema_config.DB_DSN
    __schema__ = schema_config.DB_SCHEMA


def create_base_model(schema_name: str):
    """
    Create a SQLAlchemy declarative base with a specific schema name.
    All models will inherit audit fields (_created, _updated).

    Args:
        schema_name: The PostgreSQL schema name to use for all tables

    Returns:
        Declarative base class configured with the specified schema and audit fields
    """

    # Create a new base that includes the audit mixin
    class RFXBaseSchema(RFXConnector.__data_schema_base__, DomainSchema):
        __abstract__ = True
        __table_args__ = {"schema": schema_name}

    return RFXBaseSchema


Base = create_base_model(config.RFX_CLIENT_SCHEMA)


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = config.RFX_CLIENT_SCHEMA
