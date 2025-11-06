import logging
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# All schema bases inherit from NCSTelehealthConnector.__data_schema_base__
# Import the connector and all schema modules to register their models
from rfx_schema import config as rfx_config
from rfx_schema import RFXConnector

# Import all schema modules to ensure their models are registered
from rfx_schema import _schema, _pgentity

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Use the shared base metadata for autogenerate
target_metadata = RFXConnector.__data_schema_base__.metadata
sync_url = rfx_config.DB_DSN.replace('+asyncpg://', '+psycopg2://')


SCHEMAS = (
    'rfx_user',
)


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


    # # # Never drop tables - only allow CREATE and ALTER operations
    # if reflected and not compare_to:
    #     # This is an existing table in the database that doesn't exist in models
    #     # Don't include it in autogenerate to prevent DROP TABLE
    #     logger.debug(f"include_object: skipping {name} because it is an existing database entity")
    #     return False

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
            version_table='rfx_schema_alembic'
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
