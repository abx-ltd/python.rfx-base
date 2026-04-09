import os

from alembic_utils.replaceable_entity import register_entities

from .views import ALL_VIEWS


def register_pg_entities(allow):
    register_entities([*ALL_VIEWS])


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
