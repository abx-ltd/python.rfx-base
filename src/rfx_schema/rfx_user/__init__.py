from .. import create_base_model, logger, config  # noqa: F401

# Use schema name from rfx_schema.config (not rfx_base.config to avoid circular imports)
# The alembic/env.py injects base_config.RFX_USER_SCHEMA into rfx_schema.config before importing this
Base = create_base_model(config.RFX_USER_SCHEMA)

# Make schema name available for foreign key references
SCHEMA = config.RFX_USER_SCHEMA
