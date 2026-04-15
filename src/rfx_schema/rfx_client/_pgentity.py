"""
RFX Client PostgreSQL View Entities
====================================
Registers database views for Alembic migrations.
"""

import os
from rfx_schema import logger
from alembic_utils.replaceable_entity import register_entities

from .views import ALL_VIEWS

def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES is disabled or not set.")
        return

    register_entities(
        [
            *ALL_VIEWS,
        ]
    )


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
