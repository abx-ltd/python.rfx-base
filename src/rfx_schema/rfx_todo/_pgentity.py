"""
RFX Discuss PostgreSQL View Entities
=====================================
Registers database views for Alembic migrations.
"""

import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.replaceable_entity import register_entities


def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES is disabled or not set.")
        return

    register_entities([])

    logger.info(f"Registered 0 PostgreSQL views for {config.RFX_TODO_SCHEMA} schema")


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
