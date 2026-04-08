import os
from rfx_schema import logger
from rfx_base import config
from rfx_schema.rfx_media import SCHEMA as MEDIA_SCHEMA

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

entry_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_entry",
    definition=f"""
    WITH RECURSIVE
    real_entries AS (
        SELECT
            e._created,
            e._creator,
            e._etag,
            e._id,
            e._updated,
            e._updater,
            e._deleted,
            e._realm,
            cb.realm_id AS realm_id,
            e.cabinet_id,
            e.parent_path,
            e.path,
            e.name,
            e.type,
            e.status,
            e.media_entry_id,
            me.filename,
            me.filehash,
            me.filemime,
            me.length,
            me.resource,
            me.resource__id,
            COALESCE(
                json_agg(t.name ORDER BY t.name) FILTER (WHERE t._id IS NOT NULL),
                '[]'::json
            ) AS tags,
            FALSE AS is_virtual
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
        JOIN "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
          ON cb._id = e.cabinet_id
         AND cb._deleted IS NULL
        LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
          ON et.entry_id = e._id
         AND et._deleted IS NULL
        LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".tag t
          ON t._id = et.tag_id
         AND t._deleted IS NULL
        LEFT JOIN "{MEDIA_SCHEMA}"."media-entry" me
          ON me._id = e.media_entry_id
        WHERE e._deleted IS NULL
        GROUP BY
            e._created,
            e._creator,
            e._etag,
            e._id,
            e._updated,
            e._updater,
            e._deleted,
            e._realm,
            cb.realm_id,
            e.cabinet_id,
            e.parent_path,
            e.path,
            e.name,
            e.type,
            e.status,
            e.media_entry_id,
            me.filename,
            me.filehash,
            me.filemime,
            me.length,
            me.resource,
            me.resource__id
    ),
    entry_paths AS (
        SELECT DISTINCT
            e.cabinet_id,
            e.path
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
        WHERE e._deleted IS NULL
          AND e.path LIKE '%/%'
    ),
    path_parts AS (
        SELECT
            ep.cabinet_id,
            string_to_array(ep.path, '/') AS parts
        FROM entry_paths ep
    ),
    virtual_builder AS (
        SELECT
            pp.cabinet_id,
            pp.parts[1] AS name,
            ''::text AS parent_path,
            pp.parts[1] AS path,
            2 AS depth,
            array_length(pp.parts, 1) AS total_depth,
            pp.parts
        FROM path_parts pp
        WHERE array_length(pp.parts, 1) >= 2

        UNION ALL

        SELECT
            vb.cabinet_id,
            vb.parts[vb.depth] AS name,
            vb.path AS parent_path,
            vb.path || '/' || vb.parts[vb.depth] AS path,
            vb.depth + 1 AS depth,
            vb.total_depth,
            vb.parts
        FROM virtual_builder vb
        WHERE vb.depth < vb.total_depth
    ),
    virtual_folders AS (
        SELECT DISTINCT
            vb.cabinet_id,
            vb.path,
            vb.name,
            vb.parent_path
        FROM virtual_builder vb
        WHERE NOT EXISTS (
            SELECT 1
            FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
            WHERE e.cabinet_id = vb.cabinet_id
              AND e.path = vb.path
              AND e._deleted IS NULL
        )
    ),
    virtual_entries AS (
        SELECT
            NOW() AS _created,
            NULL::uuid AS _creator,
            NULL::text AS _etag,
            (
                substr(md5(vf.cabinet_id::text || ':' || vf.path), 1, 8) || '-' ||
                substr(md5(vf.cabinet_id::text || ':' || vf.path), 9, 4) || '-' ||
                substr(md5(vf.cabinet_id::text || ':' || vf.path), 13, 4) || '-' ||
                substr(md5(vf.cabinet_id::text || ':' || vf.path), 17, 4) || '-' ||
                substr(md5(vf.cabinet_id::text || ':' || vf.path), 21, 12)
            )::uuid AS _id,
            NOW() AS _updated,
            NULL::uuid AS _updater,
            NULL::timestamp with time zone AS _deleted,
            cb._realm,
            cb.realm_id,
            vf.cabinet_id,
            vf.parent_path,
            vf.path,
            vf.name,
            'FOLDER'::"{config.RFX_DOCMAN_SCHEMA}".entrytypeenum AS type,
            NULL::"{config.RFX_DOCMAN_SCHEMA}".entrystatusenum AS status,
            NULL::uuid AS media_entry_id,
            NULL::text AS filename,
            NULL::text AS filehash,
            NULL::text AS filemime,
            NULL::bigint AS length,
            NULL::text AS resource,
            NULL::uuid AS resource__id,
            '[]'::json AS tags,
            TRUE AS is_virtual
        FROM virtual_folders vf
        JOIN "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
          ON cb._id = vf.cabinet_id
         AND cb._deleted IS NULL
    )
    SELECT * FROM real_entries
    UNION ALL
    SELECT * FROM virtual_entries;
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
            entry_view,
            tag_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
