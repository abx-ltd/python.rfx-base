from fluvius.data import DomainSchema, SqlaDriver
from .._meta import config as schema_config
from rfx_base import config


class RFXDocmanConnector(SqlaDriver):
    __db_dsn__ = schema_config.RFX_DOCMAN_DB_DSN
    __schema__ = config.RFX_DOCMAN_SCHEMA


class Base(RFXDocmanConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": config.RFX_DOCMAN_SCHEMA}


class PolicyBase(RFXDocmanConnector.__data_schema_base__):
    __abstract__ = True
    __table_args__ = {"schema": config.RFX_POLICY_SCHEMA, "info": {"is_view": True}}


class TableBase(Base):
    __abstract__ = True


class CoreTableBase(RFXDocmanConnector.__data_schema_base__):
    """Base for technical tables without DomainSchema audit/id mixins."""

    __abstract__ = True
    __table_args__ = {"schema": config.RFX_DOCMAN_SCHEMA}


SCHEMA = config.RFX_DOCMAN_SCHEMA
RFX_POLICY_SCHEMA = config.RFX_POLICY_SCHEMA

# Ensure ORM schemas and view maps register when module loads.
from . import _schema  # noqa: F401
from . import _viewmap  # noqa: F401
from . import _pgentity  # noqa: F401
