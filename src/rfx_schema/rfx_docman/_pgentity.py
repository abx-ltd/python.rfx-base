import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities
from .types import RealmMetaKeyEnum

realm_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_realm",
    definition=f"""
    SELECT
        r._created,
        r._creator,
        r._deleted,
        r._etag,
        r._id,
        r._updated,
        r._updater,
        r._realm,
        r.name,
        r.description,
        r.icon,
        r.color,
        COALESCE(
            (
                SELECT json_object_agg(m.key, m.value)
                FROM "{config.RFX_DOCMAN_SCHEMA}".realm_meta m
                WHERE m.realm_id = r._id
                  AND m._deleted IS NULL
                  AND m.key = ANY (
                      ARRAY[
                          '{RealmMetaKeyEnum.REALM.value}',
                          '{RealmMetaKeyEnum.SHELF.value}',
                          '{RealmMetaKeyEnum.CATEGORY.value}',
                          '{RealmMetaKeyEnum.CABINET.value}'
                      ]::"{config.RFX_DOCMAN_SCHEMA}".realmmetakeyenum[]
                  )
            ),
            '{{}}'::json
        ) AS realm_meta,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".shelf s
            WHERE s.realm_id = r._id
              AND s._deleted IS NULL
        ) AS shelf_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".realm r
    WHERE r._deleted IS NULL;
    """,
)

shelf_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_shelf",
    definition=f"""
    SELECT
        s._created,
        s._creator,
        s._deleted,
        s._etag,
        s._id,
        s._updated,
        s._updater,
        s._realm,
        s.realm_id,
        s.code,
        s.name,
        s.description,
        COUNT(c._id)::int AS category_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".shelf s
    LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".category c
           ON c.shelf_id = s._id
          AND c._deleted IS NULL
    WHERE s._deleted IS NULL
    GROUP BY
        s._created,
        s._creator,
        s._deleted,
        s._etag,
        s._id,
        s._updated,
        s._updater,
        s._realm,
        s.realm_id,
        s.code,
        s.name,
        s.description;
    """,
)

category_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_category",
    definition=f"""
    SELECT
        c._created,
        c._creator,
        c._deleted,
        c._etag,
        c._id,
        c._updated,
        c._updater,
        c._realm,
        c.realm_id,
        c.shelf_id,
        c.code,
        c.name,
        c.description,
        COUNT(cb._id)::int AS cabinet_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".category c
    LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
           ON cb.category_id = c._id
          AND cb._deleted    IS NULL
    WHERE c._deleted IS NULL
    GROUP BY
        c._created,
        c._creator,
        c._deleted,
        c._etag,
        c._id,
        c._updated,
        c._updater,
        c._realm,
        c.realm_id,
        c.shelf_id,
        c.code,
        c.name,
        c.description;
    """,
)

cabinet_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_cabinet",
    definition=f"""
    SELECT
        cb._created,
        cb._creator,
        cb._deleted,
        cb._etag,
        cb._id,
        cb._updated,
        cb._updater,
        cb._realm,
        cb.realm_id,
        cb.category_id,
        cb.code,
        cb.name,
        cb.description,
        COUNT(e._id)::int AS entry_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
    LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".entry e
           ON e.cabinet_id = cb._id
          AND e._deleted   IS NULL
    WHERE cb._deleted IS NULL
    GROUP BY
        cb._created,
        cb._creator,
        cb._deleted,
        cb._etag,
        cb._id,
        cb._updated,
        cb._updater,
        cb._realm,
        cb.realm_id,
        cb.category_id,
        cb.code,
        cb.name,
        cb.description;
    """,
)

tag_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_tag",
    definition=f"""
    SELECT DISTINCT ON (t._id, e.cabinet_id)
        t._created,
        t._creator,
        t._deleted,
        t._etag,
        t._id,
        t._updated,
        t._updater,
        t._realm,
        t.realm_id,
        e.cabinet_id,
        t.name,
        t.color,
        t.icon
    FROM "{config.RFX_DOCMAN_SCHEMA}".tag t
    JOIN "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
      ON et.tag_id = t._id
    JOIN "{config.RFX_DOCMAN_SCHEMA}".entry e
      ON e._id      = et.entry_id
     AND e._deleted IS NULL
    WHERE t._deleted IS NULL

    UNION

    SELECT
        t._created,
        t._creator,
        t._deleted,
        t._etag,
        t._id,
        t._updated,
        t._updater,
        t._realm,
        t.realm_id,
        NULL::uuid AS cabinet_id,
        t.name,
        t.color,
        t.icon
    FROM "{config.RFX_DOCMAN_SCHEMA}".tag t
    WHERE t._deleted IS NULL
      AND NOT EXISTS (
          SELECT 1
          FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et2
          JOIN "{config.RFX_DOCMAN_SCHEMA}".entry e2
            ON e2._id      = et2.entry_id
           AND e2._deleted IS NULL
          WHERE et2.tag_id = t._id
      );
    """,
)


def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES for rfx_docman is disabled or not set.")
        return
    register_entities(
        [
            realm_view,
            shelf_view,
            category_view,
            cabinet_view,
            tag_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
