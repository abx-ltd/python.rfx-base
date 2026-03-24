import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities

realm_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_realm",
    definition=f"""
    SELECT
        r.*,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',            s._id,
                        'realm_id',       s.realm_id,
                        'code',           s.code,
                        'name',           s.name,
                        'description',    s.description,
                        'category_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".category c
                            WHERE c.shelf_id = s._id
                              AND c._deleted IS NULL
                        ),
                        'cabinet_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
                            WHERE cb.realm_id = s.realm_id
                              AND cb._deleted IS NULL
                              AND cb.category_id IN (
                                  SELECT c2._id
                                  FROM "{config.RFX_DOCMAN_SCHEMA}".category c2
                                  WHERE c2.shelf_id = s._id
                                    AND c2._deleted IS NULL
                              )
                        ),
                        'entry_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
                            WHERE e._deleted IS NULL
                              AND e.cabinet_id IN (
                                  SELECT cb2._id
                                  FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb2
                                  WHERE cb2.realm_id = s.realm_id
                                    AND cb2._deleted IS NULL
                                    AND cb2.category_id IN (
                                        SELECT c3._id
                                        FROM "{config.RFX_DOCMAN_SCHEMA}".category c3
                                        WHERE c3.shelf_id = s._id
                                          AND c3._deleted IS NULL
                                    )
                              )
                        )
                    )
                    ORDER BY s.code
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".shelf s
                WHERE s.realm_id = r._id
                  AND s._deleted IS NULL
            ),
            '[]'::json
        ) AS shelves
    FROM "{config.RFX_DOCMAN_SCHEMA}".realm r
    WHERE r._deleted IS NULL;
    """,
)

shelf_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_shelf",
    definition=f"""
    SELECT
        s.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".category c
            WHERE c.shelf_id = s._id AND c._deleted IS NULL
        ) AS category_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
            WHERE cb.realm_id = s.realm_id 
              AND cb._deleted IS NULL
              AND cb.category_id IN (
                  SELECT c2._id 
                  FROM "{config.RFX_DOCMAN_SCHEMA}".category c2 
                  WHERE c2.shelf_id = s._id AND c2._deleted IS NULL
              )
        ) AS cabinet_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
            WHERE e._deleted IS NULL
              AND e.cabinet_id IN (
                  SELECT cb2._id
                  FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb2
                  WHERE cb2.realm_id = s.realm_id
                    AND cb2._deleted IS NULL
                    AND cb2.category_id IN (
                        SELECT c3._id
                        FROM "{config.RFX_DOCMAN_SCHEMA}".category c3
                        WHERE c3.shelf_id = s._id AND c3._deleted IS NULL
                    )
              )
        ) AS entry_count
        ,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',           c._id,
                        'realm_id',      c.realm_id,
                        'shelf_id',      c.shelf_id,
                        'code',          c.code,
                        'name',          c.name,
                        'description',   c.description,
                        'cabinet_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
                            WHERE cb.category_id = c._id
                              AND cb._deleted IS NULL
                        ),
                        'entry_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
                            WHERE e._deleted IS NULL
                              AND e.cabinet_id IN (
                                  SELECT cb2._id
                                  FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb2
                                  WHERE cb2.category_id = c._id
                                    AND cb2._deleted IS NULL
                              )
                        )
                    )
                    ORDER BY c.code
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".category c
                WHERE c.shelf_id = s._id
                  AND c._deleted IS NULL
            ),
            '[]'::json
        ) AS categories
    FROM "{config.RFX_DOCMAN_SCHEMA}".shelf s;
    """,
)

category_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_category",
    definition=f"""
    SELECT
        c.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
            WHERE cb.category_id = c._id AND cb._deleted IS NULL
        ) AS cabinet_count,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
            WHERE e._deleted IS NULL
              AND e.cabinet_id IN (
                  SELECT cb2._id
                  FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb2
                  WHERE cb2.category_id = c._id AND cb2._deleted IS NULL
              )
        ) AS entry_count
        ,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',         cb._id,
                        'realm_id',    cb.realm_id,
                        'category_id', cb.category_id,
                        'code',        cb.code,
                        'name',        cb.name,
                        'description', cb.description,
                        'entry_count', (
                            SELECT COUNT(*)::int
                            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
                            WHERE e.cabinet_id = cb._id
                              AND e._deleted IS NULL
                        )
                    )
                    ORDER BY cb.code
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
                WHERE cb.category_id = c._id
                  AND cb._deleted IS NULL
            ),
            '[]'::json
        ) AS cabinets
    FROM "{config.RFX_DOCMAN_SCHEMA}".category c;
    """,
)

cabinet_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_cabinet",
    definition=f"""
    SELECT
        cb.*,
        (
            SELECT COUNT(*)::int
            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
            WHERE e.cabinet_id = cb._id AND e._deleted IS NULL
        ) AS entry_count,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',        e._id,
                        'cabinet_id', e.cabinet_id,
                        'path',       e.path,
                        'name',       e.name,
                        'type',       e.type,
                        'size',       e.size,
                        'mime_type',  e.mime_type,
                        'author',     e.author,
                        'parent_path', COALESCE(SUBSTRING(e.path FROM '(.*)/'), ''),
                        'tags',       COALESCE(
                            (
                                SELECT json_agg(
                                    json_build_object(
                                        '_id',   t._id,
                                        'name',  t.name,
                                        'color', t.color,
                                        'icon',  t.icon
                                    )
                                    ORDER BY t.name
                                )
                                FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
                                JOIN "{config.RFX_DOCMAN_SCHEMA}".tag t ON t._id = et.tag_id
                                                                       AND t._deleted IS NULL
                                WHERE et.entry_id = e._id
                            ),
                            '[]'::json
                        )
                    )
                    ORDER BY e.path
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
                WHERE e.cabinet_id = cb._id
                  AND e._deleted IS NULL
            ),
            '[]'::json
        ) AS entries
    FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb;
    """,
)

entry_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_entry",
    definition=f"""
    SELECT
        e.*,
        COALESCE(SUBSTRING(e.path FROM '(.*)/'), '') AS parent_path,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',    t._id,
                        'name',  t.name,
                        'color', t.color,
                        'icon',  t.icon
                    )
                    ORDER BY t.name
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
                JOIN "{config.RFX_DOCMAN_SCHEMA}".tag         t  ON t._id = et.tag_id
                                                                   AND t._deleted IS NULL
                WHERE et.entry_id = e._id
            ),
            '[]'::json
        ) AS tags
    FROM "{config.RFX_DOCMAN_SCHEMA}".entry e;
    """,
)

tag_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_tag",
    definition=f"""
    SELECT
        t.*,
        COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        '_id',        e._id,
                        'name',       e.name,
                        'path',       e.path,
                        'type',       e.type,
                        'cabinet_id', e.cabinet_id
                    )
                    ORDER BY e.path
                )
                FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
                JOIN "{config.RFX_DOCMAN_SCHEMA}".entry      e  ON e._id = et.entry_id
                                                                  AND e._deleted IS NULL
                WHERE et.tag_id = t._id
            ),
            '[]'::json
        ) AS entries
    FROM "{config.RFX_DOCMAN_SCHEMA}".tag t
    WHERE t._deleted IS NULL;
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
            entry_view,
            tag_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
