"""
RFX Client PostgreSQL View Entities
====================================
Registers database views for Alembic migrations.
"""

import os
from alembic_utils.replaceable_entity import register_entities

from .views import ALL_VIEWS

def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""

    register_entities(
        [
            *ALL_VIEWS,
        ]
    )


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
