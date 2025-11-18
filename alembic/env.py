import logging
import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# STEP 1: Load base config (which triggers setupModule and reads from .ini files)
from rfx_base import config as base_config

# STEP 2: Import RFXConnector and schema modules (they will use rfx_base.config directly)
from rfx_schema import DOMAIN_CONNECTORS, config as schema_config
from rfx_schema import _schema, _pgentity

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

sync_url = schema_config.DB_DSN.replace('+asyncpg://', '+psycopg2://')

# All available schemas
DOMAIN_SCHEMAS = {
    'user': base_config.RFX_USER_SCHEMA,
    'policy': base_config.RFX_POLICY_SCHEMA,
    'message': base_config.RFX_MESSAGE_SCHEMA,
    'media': base_config.RFX_MEDIA_SCHEMA,
    'notify': base_config.RFX_NOTIFY_SCHEMA,
    'client': base_config.RFX_CLIENT_SCHEMA,
    'discuss': base_config.RFX_DISCUSS_SCHEMA,
}

# Get schema filter from environment variable
# Format: comma-separated list like "user,message" or "all" (default)
# Set via: ALEMBIC_SCHEMA_FILTER=user,message alembic revision --autogenerate -m "message"
# Or use the just commands: just mig-autogen "message" user,message
schema_filter = os.getenv('ALEMBIC_SCHEMA_FILTER', 'all')
if schema_filter and schema_filter != 'all':
    schema_names = [s.strip() for s in schema_filter.split(',') if s.strip() in DOMAIN_SCHEMAS]
else:
    schema_names = list(DOMAIN_SCHEMAS.keys())

if not schema_names:
    logger.warning("⚠️  No valid schemas selected, defaulting to all")
    schema_names = list(DOMAIN_SCHEMAS.keys())

SCHEMAS = tuple(DOMAIN_SCHEMAS[name] for name in schema_names)
selected_connectors = [DOMAIN_CONNECTORS[name] for name in schema_names if name in DOMAIN_CONNECTORS]
target_metadata = [connector.__data_schema_base__.metadata for connector in selected_connectors]

logger.info(f"📋 Using schemas: {schema_names} -> {SCHEMAS}")


def include_server_default(inspector, table, column, column_default, metadata_default, **kw):
    # Return False to skip comparison for this column
    if column.name in ("_created", "_updated", "_etag"):
        return False
    return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function to control which objects are included in autogenerate.

    This prevents alembic from generating DROP TABLE statements and
    other destructive operations during autogenerate.
    """
    if type_ in ('grant_table', 'extension'):
        return False

    if type_ in ('table', 'view') and object.schema not in SCHEMAS:
        return False

    if hasattr(object, 'info') and object.info.get('is_view'):
        logger.warning(f"include_object: skipping {name} because it is a view")
        return False

    # For other objects, use default behavior
    return True
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Convert asyncpg URL to synchronous psycopg2 for alembic
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        compare_type=True,
        include_server_default=include_server_default,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Convert asyncpg URL to synchronous psycopg2 for alembic
    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            compare_type=True,
            include_server_default=include_server_default,
            version_table='rfx_schema_version'
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
