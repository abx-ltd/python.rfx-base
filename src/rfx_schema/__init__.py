from ._meta import config, logger

from datetime import datetime, UTC
from sqlalchemy import create_engine, MetaData, Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from fluvius.data import DomainSchema, SqlaDriver


# --- Connector and Base Schema ---
class RFXConnector(SqlaDriver):
    __db_dsn__ = config.DB_DSN
    __schema__ = config.DB_SCHEMA


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
