
import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities

shelf_view = PGView(
    schema=config.RFX_DOCUMENT_SCHEMA,
    signature="_shelf",
    definition=f"""
    SELECT
        s.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".category c
            WHERE c.shelf_id = s._id AND c._deleted IS NULL
        ) AS category_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".cabinet cb
            WHERE cb.realm_id = s.realm_id 
              AND cb._deleted IS NULL
              AND cb.category_id IN (
                  SELECT c2._id 
                  FROM "{config.RFX_DOCUMENT_SCHEMA}".category c2 
                  WHERE c2.shelf_id = s._id AND c2._deleted IS NULL
              )
        ) AS cabinet_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".entry e
            WHERE e._deleted IS NULL
              AND e.cabinet_id IN (
                  SELECT cb2._id
                  FROM "{config.RFX_DOCUMENT_SCHEMA}".cabinet cb2
                  WHERE cb2.realm_id = s.realm_id
                    AND cb2._deleted IS NULL
                    AND cb2.category_id IN (
                        SELECT c3._id
                        FROM "{config.RFX_DOCUMENT_SCHEMA}".category c3
                        WHERE c3.shelf_id = s._id AND c3._deleted IS NULL
                    )
              )
        ) AS entry_count
    FROM "{config.RFX_DOCUMENT_SCHEMA}".shelf s;
    """
)

category_view = PGView(
    schema=config.RFX_DOCUMENT_SCHEMA,
    signature="_category",
    definition=f"""
    SELECT
        c.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".cabinet cb
            WHERE cb.category_id = c._id AND cb._deleted IS NULL
        ) AS cabinet_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".entry e
            WHERE e._deleted IS NULL
              AND e.cabinet_id IN (
                  SELECT cb2._id
                  FROM "{config.RFX_DOCUMENT_SCHEMA}".cabinet cb2
                  WHERE cb2.category_id = c._id AND cb2._deleted IS NULL
              )
        ) AS entry_count
    FROM "{config.RFX_DOCUMENT_SCHEMA}".category c;
    """
)

cabinet_view = PGView(
    schema=config.RFX_DOCUMENT_SCHEMA,
    signature="_cabinet",
    definition=f"""
    SELECT
        cb.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCUMENT_SCHEMA}".entry e
            WHERE e.cabinet_id = cb._id AND e._deleted IS NULL
        ) AS entry_count
    FROM "{config.RFX_DOCUMENT_SCHEMA}".cabinet cb;
    """
)

def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info('REGISTER_PG_ENTITIES for rfx_document is disabled or not set.')
        return
    register_entities([
        shelf_view,
        category_view,
        cabinet_view,
    ])

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))
